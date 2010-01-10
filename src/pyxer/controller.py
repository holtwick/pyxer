# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from webob import Request, Response
from paste.registry import StackedObjectProxy

import logging
log = logging.getLogger(__name__)

c = StackedObjectProxy(name = "C")
g = StackedObjectProxy(name = "G")
h = StackedObjectProxy(name = "H")

# cache = StackedObjectProxy(name="Cache")
request = req = StackedObjectProxy(name = "Request")
response = resp = StackedObjectProxy(name = "Response")
session = StackedObjectProxy(name = "Session")
config = StackedObjectProxy(name = "Config")

class Decorator(object):

    """
    A helper for creating decorators. It can be called these ways:

    @Decorator
    @Decorator()
    @Decorator(some=1, args=2)

    The keyword arguments are then available in the wrapper() method
    via self.kw. Please overload the wrapper method.
    """

    def __init__(self, func_ = None, **kw):
        self.func = func_
        self.kw = kw
        if self.func is not None:
            self.func.__pyxer_controller = True

    def __call__(self, *a, **kw):
        if self.func is None:
            self.func, a = a[0], a[1:]
            return self.wrapper
        return self.wrapper(*a, **kw)

    def wrapper(self, *a, **kw):
        # To be overloaded
        log.error("Decorator.wrapper should be overloaded")
        return self.func(*a, **kw)

class Controller(Decorator):

    """
    The overloaded wrapper method prepares usual stuff and then calls render
    which has to be overloaded by the controller implementations.
    """

    def call(self, *a, **kw):
        return self.func(*a, **kw)

    def wrapper(self, *a, **kw):

        # Execute controller and get its result
        result = self.call(*a, **kw)
        log.debug("Controller call %r (%r %r) = %r", self.func, a, kw, repr(result)[:40])

        # Ask render what to do with it
        if result is not response:
            result = self.render(result, **self.kw)
            log.debug("Render call %r (%r) = %r", self.render, self.kw, repr(result)[:40])
    
            # Publish result        
            if isinstance(result, unicode):
                response.charset = 'utf-8'
                response.unicode_body = result
            else:
                response.body = result

        return response(request.environ, request.start_response)

    def render(self, result, **kw):
        # To be overloaded
        log.error("Controller.render should be overloaded")
        return result

def isController(obj):
    " Little helper to recognize controllers "
    return (
        isinstance(obj, Controller) or
        issubclass(getattr(obj, "im_class", object), Controller))

def getObjectsFullName(obj):
    import inspect
    if isController(obj):
        if isinstance(obj, Controller):
            obj = obj.func
        else:
            obj = obj.im_self.func
    if hasattr(obj, "__name__"):
        return inspect.getmodule(obj).__name__ + ":" + obj.__name__
    return ""

if __name__ == "__main__":

    class mycontroller(Controller):

        def render(self, result, value = None):
            print "RENDER", result, value
            return result

    class my2controller(mycontroller):
        pass

    @mycontroller
    def testa(v, w):
        return v

    @mycontroller(value = 999)
    def testb(v, w):
        return v

    @mycontroller()
    def testc(v, w):
        return v

    def testd(v, w):
        return v

    @my2controller
    def teste(v, w):
        return v

    assert isController(testa) == True
    assert isController(testb) == True
    assert isController(testc) == True
    assert isController(testd) == False
    assert isController(teste) == True

    #assert testa(111, 111) == 111
    #assert testb(222, 222) == 222
    #assert testc(333, 333) == 333
    #assert testd(444, 444) == 444

    assert getObjectsFullName(testa) == "__main__:testa"
    assert getObjectsFullName(testb) == "__main__:testb"
    assert getObjectsFullName(testc) == "__main__:testc"
    assert getObjectsFullName(testd) == "__main__:testd"
    assert getObjectsFullName(None) == ""

