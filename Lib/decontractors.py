# -*- coding: utf-8 -*-
#
# Decontractors - A Programming by Contract implementation using Decorators
# http://thp.io/2011/decontractors/
#
# Copyright (c) 2011 Thomas Perl <m@thp.io>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""A Programming by Contract implementation using Decorators"""

# Will be parsed by setup.py to determine package metadata
__author__ = 'Thomas Perl <m@thp.io>'
__version__ = '0.2'
__website__ = 'http://thp.io/2011/decontractors/'
__license__ = 'Modified BSD License'

# TODO: Will setting this in one place set it everywhere?
DECONTRACTORS_ENABLED = True

def use_decontractors(b):
    global DECONTRACTORS_ENABLED
    DECONTRACTORS_ENABLED = b

import functools
import inspect

class DecontractorException(BaseException):
    def __init__(self, decontractor, locals, verbose=True):
        if verbose:
            BaseException.__init__(self, str(locals))
        else:
            BaseException.__init__(self)
        self.decontractor = decontractor
        self.locals = locals

class PreconditionViolation(DecontractorException): pass
class PostconditionViolation(DecontractorException): pass

class Decontractor(object):
    ARGSPEC = '__decontractor_argspec__'
    OLDGLOBALS = '__decontractor_inherited_globals__'

    def __init__(self, check, globals=None):
        self.globals = globals
        self.check = check

    def verify(self, locals):
        return self.check_before(locals)

    def check_before(self, before, globals):
        return True

    def check_after(self, result, before, after, globals):
        return True

    def build_locals(self, f, args, kwargs):
        argspec = getattr(f, self.ARGSPEC)
        if len(args) > len(argspec.args):
            varargs = args[len(args):]
            args = args[:len(args)]
        else:
            varargs = []

        if self.globals is not None:
            globals = self.globals
        elif hasattr(f, self.OLDGLOBALS):
            globals = getattr(f, self.OLDGLOBALS)
        else:
            globals = {}

        locals= dict(zip(argspec.args, args))
        if argspec.varargs is not None:
            locals.update({argspec.varargs: varargs})
        if argspec.keywords is not None:
            locals.update({argspec.keywords: kwargs})
        locals.update(kwargs)

        return globals, locals

    def __call__(self, f):
        if not DECONTRACTORS_ENABLED:
            return f

        if not hasattr(f, self.ARGSPEC):
            argspec = inspect.getargspec(f)
            setattr(f, self.ARGSPEC, argspec)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            globals, before = self.build_locals(f, args, kwargs)
            self.check_before(before, globals)
            result = f(*args, **kwargs)
            _, after = self.build_locals(f, args, kwargs)
            self.check_after(result, before, after, globals)
            return result

        if self.globals:
            setattr(wrapper, self.OLDGLOBALS, self.globals)

        return wrapper


class Invariant(Decontractor):
    def check_before(self, before, globals):
        if before is None and globals is None:
            result = self.check()
        else:
            if globals:
                vars = globals.copy()
                if before:
                    vars.update(before)
            else:
                vars = before.copy()

            result = eval(self.check.__code__, vars)

        if not result:
            raise PreconditionViolation(self, before)

        return result

    def check_after(self, result, before, after, globals):
        if before is None and after is None and globals is None:
            result = self.check()
        else:
            locals = dict(after)
            locals.update({'__return__': result, '__old__': before})
            if globals:
                globals_copy = globals.copy()
                globals_copy.update(locals.copy())
                result = eval(self.check.__code__, globals_copy)
            else:
                result = eval(self.check.__code__, locals.copy())

        if not result:
            raise PostconditionViolation(self, locals)

        return result


class Postcondition(Invariant):
    def check_before(self, before, globals):
        return True


class Precondition(Invariant):
    def check_after(self, result, before, after, globals):
        return True


class Contract(Invariant):
    def __init__(self, precondition, invariant, postcondition):
        Invariant.__init__(self, precondition)
        self._precondition = precondition
        self._invariant = invariant
        self._postcondition = postcondition

    def __enter__(self):
        self.check = self._precondition
        self.check_before(None, None)
        return self

    def __call__(self):
        self.check = self._invariant
        self.check_before(None, None)

    def __exit__(self, exc_type, exc_value, traceback):
        self.check = self._postcondition
        self.check_after(None, None, None, None)

