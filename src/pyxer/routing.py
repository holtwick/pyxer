# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from webob import Request
from webob import exc

from pyxer.controller import \
    Controller, isController, c, g, h, config, \
    session, response, request, resp, req

import re
# import urllib
import copy
import sys
import types
import os.path

import paste.fileapp

import logging
log = logging.getLogger(__name__)

# Static file handling

def static():
    tail = req.urlvars["static"]
    path = os.path.join(req.urlvars["pyxer.path"], tail)
    # Is it a folder? Or a link?
    if os.path.isdir(path) or os.path.islink(path):
        if (not tail) or tail.endswith("/"):
            path = os.path.join(path, "index.html")
        elif tail:
            location = (req.environ["PATH_INFO"] + "/")

            # XXX not tested!
            if request.environ.has_key("HTTP_X_FORWARDED_HOST"):
                # log.debug("URL (x) %r %r", obj, request.environ["HTTP_X_FORWARDED_HOST"])
                location = "http://" + request.environ["HTTP_X_FORWARDED_HOST"]

            raise exc.HTTPMovedPermanently(location = location).exception
    if not os.path.isfile(path):
        raise exc.HTTPNotFound().exception
    return paste.fileapp.FileApp(path)(request.environ, request.start_response)

static.iscontroller = True

class ModuleHook:

    " Constructor and destructor for modules "

    def __init__(self, module):
        self.module = module
        try:
            module.__init__()
        except:
            pass

    def __del__(self):
        try:
            self.module.__del__()
        except:
            pass
        del self.module

var_regex = re.compile(r'''
    \{              # The exact character "{"
    (\w+)           # The variable name (restricted to a-z, 0-9, _)
    (?::([^}]+))?   # The optional :regex part
    \}              # The exact character "}"
    ''', re.VERBOSE)

def template_to_regex(template, ismodule=False):
    regex = ''
    last_pos = 0
    for match in var_regex.finditer(template):
        regex += re.escape(template[last_pos:match.start()])
        var_name = match.group(1)
        expr = match.group(2) or '[^/]+'
        expr = '(?P<%s>%s)' % (var_name, expr)
        regex += expr
        last_pos = match.end()
    regex += re.escape(template[last_pos:])
    if ismodule:
        if not regex.endswith("\/"):
            regex += "\/"
        regex = '^%s' % regex
    else:
        regex = '^%s$' % regex
    return regex

'''
def url(*segments, **vars):
    base_url = get_request().application_url
    path = '/'.join(str(s) for s in segments)
    if not path.startswith('/'):
        path = '/' + path
    if vars:
        path += '?' + urllib.urlencode(vars)
    return base_url + path
'''

class RouteObject(object):

    def __init__(self,
            template,
            module = None,
            controller = None,
            name = None,
            vars = {}):
        if module and controller:
            raise Exception("Route to module and controller the same time is not allowed")
        # log.debug("Template for routing %r", template)
        self.template = re.compile(template) #template_to_regex
        self.module = module
        self.controller = controller
        self.name = name
        self.vars = copy.copy(vars)
        self.vars["controller"] = self.controller
        self.vars["module"] = self.module

    def __repr__(self):
        return "<RouteObject '%s'; pattern '%s'>" % (
            self.name, self.template.pattern)

    __str__ = __repr__

class Router(object):

    def __init__(self, module = None, prefix = "", use_default = True, do_reload = False):
        self.module = None
        self.module_name = None
        self.prefix = prefix
        self.routes = []
        self.routes_default = []
        self.do_reload = do_reload

        # Set first module
        self.set_module(module)

        # This should only apply to the firt router ever
        if self.module and hasattr(self.module, "router"):
            self.routes = self.module.router.routes

        # Default routings
        if use_default:
            # /
            self.add_default("^$",
                controller = "index",
                name = "_action_index")
            # /demo, /demo.html, /demo.htm, /demo.xml
            self.add_default("^(?P<controller>[^\/\.]+?)(\.html?|\.xml)?$",
                name = "_action")
            # /demo/
            self.add_default("^(?P<module>[^\/\.]+?)\/",
                name = "_module")
            # demo.py
            self.add_default("^[^\/\.]+?\.(py[co]?)$",
                controller = None,
                module = None,
                name = "_ignore_py")
            # demo.xyz
            #self.add_default("^(?P<static>[^\/\.]+?\.[^\/\.]+?)$",
            #    controller = "static", # "static"
            #    name = "_static")
            # demo-xyz-abc
            self.add_default("^[^\/\.]*?$",
                controller = "default",
                name = "_action_default")
            #
            self.add_default("^(?P<static>.*?)$",
                controller = "static",
                name = "_static_all")
            self.add_default("^(?P<static>.*?)$",
                controller = static,
                name = "_static_all")

    def init_module(self, module, hook =  False):
        " If needed reload a module and apply module hook if needed or forced to "
        if self.do_reload:
            module = reload(module)
            module.__module_hook__ = ModuleHook(module)
        elif hook:
            module.__module_hook__ = ModuleHook(module)
        return module

    def load_module(self, *names):
        " Load module "
        name = ".".join(names)
        if sys.modules.has_key(name):
            return self.init_module(sys.modules[name])
        try:
            __import__(name)
            return self.init_module(sys.modules[name], True)
        except ImportError, msg:
            # Try to filter import errors that are within the loaded module
            if name and (not (str(msg).endswith("." + names[-1]) or str(msg).endswith(" " + names[-1]))):
                log.exception("Error while importing module")
                raise
        return None

    def set_module(self, module = None):
        " Set module and its name "
        if module is not None:
            if isinstance(module, basestring):
                self.module = self.load_module(module)
            else:
                self.module = module
            self.module_name = self.module.__name__
        return self

    def add(self, template, **kw):
        self.routes.append(RouteObject(template_to_regex(template, kw.get("module", None)), **kw))
        return self
    
    def add_re(self, template, **kw):
        self.routes.append(RouteObject(template, **kw))
        return self
    
    def add_default(self, template, **kw):
        self.routes_default.append(RouteObject(template, **kw))
        return self

    def match(self, path):
        if path.startswith("/"):
            path = path[1:]
        obj, vars = self._match(path)
        return obj, vars

    def _match(self, path, module = None, urlvars = {}):
        # Normalize module infos
        self.set_module(module)
        # Search
        for route in self.routes + self.routes_default:
            match = route.template.match(path)
            # log.debug("Try to match %r %r", route, match)
            if match:
                urlvars = {}
                urlvars.update(route.vars)
                urlvars.update(match.groupdict())
                tail = path[match.end():].lstrip("/")
                urlvars["pyxer.tail"] = tail
                urlvars["pyxer.match"] = path[match.start():match.end()]
                urlvars["pyxer.path"] = os.path.dirname(os.path.abspath(self.module.__file__))

                log.debug("Matched %r %r %r %r", path, route, urlvars, route.vars)

                # Abort matching
                if urlvars["module"] is None and urlvars["controller"] is None:
                    return (None, None)

                # Handle module
                if urlvars["module"] is not None:
                    obj = urlvars["module"]

                    # If it is a module go ahead
                    if isinstance(obj, types.ModuleType):
                        module = obj

                    # If it is a string it could be a module or a
                    elif isinstance(obj, basestring):

                        # Load module relatively or absolute
                        module = (
                            self.load_module(self.module_name, obj)
                            or self.load_module(obj))

                        if module is None:
                            log.debug("Module %r not found", obj)
                            continue

                    # If it is anything else, let the caller decide what to do
                    else:
                        raise Exception("No module")

                    # Let's see if they need a Router()
                    if not hasattr(module, "router"):
                        module.router = Router(module)

                    # The router goes to the next round
                    return module.router._match(tail, module) #, urlvars)

                # Handle controller
                if urlvars["controller"] is not None:
                    obj = urlvars["controller"]

                    if isinstance(obj, basestring):
                        if hasattr(self.module, obj):
                            obj = getattr(self.module, obj)

                    if hasattr(obj, "iscontroller") or isController(obj):
                        return obj, urlvars
                    else:
                        log.debug("Object %r is not a controller", obj)

                    continue

        return (None, None)

"""
- urlvars nicht bei modulen möglich, oder doch z.B. für sprachen?
- subdomain ermöglichen, z.b. für sprachwechsel?
- genaues macthing nicht test -> test/
- '' oder '*' einführen, steht nur alleine und heisst: der gnaze rest
- umleitung zu default static oder als parameter? ('', static)
- url_for equivalent
- benannte url schemata
- module, controller, action heissen alle object und können auch strings sein
- explizite actions in den urlvars {action:*}
- redirects, auch zu großen domains: ('google', redirect('google.com')
- auf für fehler error(404)
"""

def testing():
    from pyxer.controller import getObjectsFullName, isController

    static = "pyxer.routing:static"

    if __name__=="__main__":
        module = "__main__"
    else:
        module = "pyxer.routing"

    data = [
        ("",                            "public:index"),
        ("/",                           "public:index"),
        ("index",                       "public:index"),
        ("/index",                      "public:index"), # slash is ignored
        ("index.htm",                   "public:index"),
        ("index.html",                  "public:index"),
        ("index.gif",                   "pyxer.routing:static", dict(static="index.gif")),

        # Without slash a module is not recognized (could be handled by 'static' though)
        ("sub1",                        'pyxer.routing:static', {'static': 'sub1'}),

        # sub1
        ("sub1/",                       "public.sub1:index"),
        ("sub1/dummy",                  "public.sub1:dummy"),
        ("sub1/dummy2",                 "public.sub1:default"),
        ("sub1/content1",               "public.sub1:content1"),
        ("sub1/content1/some",          "public.sub1:content1", dict(name="some")),
        ("sub1/content2/some",          "public.sub1:content2", dict(name="some")),
        ("sub1/content1/some/more",     "public.sub1:content1", dict(name="some/more")),
        ("sub1/content2/some/more",     'pyxer.routing:static', {'static': 'content2/some/more'}),

        # Doesn't match at all and is therefore passed to 'static'
        ("/some/path/index.gif",        "pyxer.routing:static", dict(static="some/path/index.gif")),

        # Referencing an external module
        ("sub1/pub2/",                  "public2:index", dict()),
        ("sub1/pub2/path/index.gif",    "pyxer.routing:static", dict(static="path/index.gif")),

        ]

    router = Router("public")
    for sample in data:
        if len(sample)==3:
            path, object_name, object_vars = sample
        else:
            path, object_name = sample
            object_vars = dict()

        obj, vars = router.match(path)
        if vars is None:
            vars = dict()
        else:
            vars.pop("controller")
            vars.pop("module")
            for k in vars.keys():
                if k.startswith("pyxer."):
                    del vars[k]
        name = getObjectsFullName(obj)
        ct = isController(obj)
        # print "%-35r %r, %r" % (path, name, vars)
        assert object_name == name
        assert object_vars == vars

if __name__ == "__main__":
    import sys
    import os.path
    sys.path.insert(0, os.path.join(__file__, "..", "..", "..", "tests"))
    testing()

    '''
    print template_to_regex('/a/static/path')
    print template_to_regex('/{year:\d\d\d\d}/{month:\d\d}/{slug}')

    route('/', controller='controllers:index')
    route('/{year:\d\d\d\d}/',
                  controller='controllers:archive')
    route('/{year:\d\d\d\d}/{month:\d\d}/',
                  controller='controllers:archive')
    route('/{year:\d\d\d\d}/{month:\d\d}/{slug}',
                  controller='controllers:view')
    route('/post', controller='controllers:post')
    '''
