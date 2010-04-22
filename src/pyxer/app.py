# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from webob import Request, Response
from webob import exc

from paste.urlparser import StaticURLParser
from paste.cascade import Cascade
# from paste.cgitb_catcher import CgitbMiddleware
from paste.registry import RegistryManager
from paste.config import ConfigMiddleware #, CONFIG
from paste.exceptions.errormiddleware import ErrorMiddleware
from paste.util.import_string import import_module

# import paste.deploy

from pyxer.base import *

import sys
import logging
import string
import mimetypes
import imp
import os
import os.path
import types
import pprint
import site
import zipimport

import logging
log = logging.getLogger(__name__)

# XXX Needed?
# sys.path = [os.getcwd()] + sys.path

_counter = 0

# The WSGI application
class PyxerApp:

    def __init__(self, base="public"):        
        self.base = base
        self.router = Router(base)

    def __call__(self, environ, start_response):

        try:

            global _counter
            _counter += 1
            log.debug("Processing pyxer call number %d", _counter)

            path = environ["PATH_INFO"]

            # Mod Python corrections
            if environ.has_key("SCRIPT_FILENAME"):
                prefix = environ["SCRIPT_FILENAME"][len(environ['DOCUMENT_ROOT']):]
                environ["WSGI_PREFIX"] = prefix
                path = path[len(prefix):]

            log.debug("Try matching %r", path)
            obj, vars = self.router.match(path)
            log.debug("For %r found %r with %r", path, obj, vars)

            # No matching
            if obj is None:
                abort(404)

            # Set globals
            if environ.has_key('paste.registry'):
                environ['paste.registry'].register(request, Request(environ))
                environ['paste.registry'].register(response, Response())
                environ['paste.registry'].register(c, AttrDict())
                if environ.has_key('beaker.session'):
                    environ['paste.registry'].register(session, environ['beaker.session'])
                else:
                    environ['paste.registry'].register(session, None)
                environ['paste.registry'].register(config, environ.get("paste.config", {}))

            request.start_response = start_response
            
            # Guess template name     
            name = None       
            if vars["controller"] == "default":
                if path.endswith("/"):
                    name = "index"
                else:
                    name = vars["pyxer.match"]
            elif isinstance(vars["controller"], basestring):
                name = vars["controller"]
            
            # and path
            request.template_url = None
            if name is not None:            
                tpath = os.path.join(vars["pyxer.path"], name + ".html")
                if os.path.isfile(tpath):
                    request.template_url = tpath
                
            request.urlvars = vars
            environ['pyxer.urlvars'] = vars
            
            environ['pyxer.urlbase'] = path[:-(len(vars["pyxer.match"]) + len(vars["pyxer.tail"]))]
            # log.info("******* %r %r %r", path, vars["pyxer.match"],  environ['pyxer.urlbase'])

            return obj()
            # obj(environ, start_response)

        # Handle HTTPException
        except exc.HTTPException, e:
            return e(environ, start_response)

# Sessions available?
SessionMiddleware = None

# Make WSGI application, wrapping sessions etc.
def make_app(global_conf={}, **app_conf):

    import os, sys
    
    # Cleanup the Python path (mainly to circumvent the systems SetupTools)
    sys.path = [path for path in sys.path if ("site-packages" not in path) and ('pyxer' not in path) and ('/Extras/lib/python' not in path)]
    
    # Add our local packages folder to the path
    import site
    
    here = app_conf.get('pyxer_here') or os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    if not os.path.isdir(os.path.join(here, 'public')):
        here = os.getcwd()
    
    site_lib = os.path.join(here, 'site-packages')
    site.addsitedir(here)
    site.addsitedir(site_lib)
    # import pkg_resources
    # import setuptools
    
    # log.info(site.__file__)
    # pprint.pprint(global_conf)
    log.debug('\n'.join(sys.path))
    
    try:        
        import beaker.middleware
        global SessionMiddleware
        SessionMiddleware = beaker.middleware.SessionMiddleware
        log.debug("Beaker successfully loaded")
    except ImportError:
        log.debug("Beaker NOT loaded")
        
    conf = AttrDict(pyxer={
        "session": "",
        "debug": False,
        "root": "public",
        })
    root = os.getcwd()
    try:
        import ConfigParser        
        filename = os.path.abspath(global_conf.get("__file__", None)) or os.path.abspath("pyxer.ini")        
        # filename = os.path.abspath("pyxer.ini" )
        root = os.path.dirname(filename)
        cfile = ConfigParser.SafeConfigParser()
        cfile.read(filename)
        for section in cfile.sections():
            if not conf.has_key(section):
                conf[section] = AttrDict()
            try:
                for name, value in cfile.items(section):
                    conf[section][name] = value
            except:
                log.exception("Config items")
        log.debug("Config: %r", conf)
    except:
        log.warning("Config file not found")

    # Add current directory to sys path    
    # site.addsitedir(root)

    # Here we expect all data
    base = os.path.join(root, "public")

    # app = App(global_conf=None, root="public", path=None, **app_conf)
    app = PyxerApp()

    if SessionMiddleware and (conf.get("pyxer.session", "beaker") == "beaker"):
        log.debug("Beaker sessions")
        if "google.appengine" in sys.modules:
            # server = SessionMiddleware(server, type='ext:google', table_name="beaker_session", cookie_expires=False)
            app = SessionMiddleware(app, 
                type='ext:google', 
                table_name='PyxerSession')
        else:
            app = SessionMiddleware(app, 
                type='dbm', 
                data_dir=os.path.join(root, 'cache'))

    app = RegistryManager(app)
    app = ConfigMiddleware(app, conf.copy())

    # app = CgitbMiddleware(app)
    if not stage:
        app = ErrorMiddleware(app, debug=True)

    #static = PyxerStatic(base)
    #app = Cascade([app, static])

    return app

# Paster EGG factory entry 
def app_factory(global_config, **local_conf):
    return make_app(global_config)

# Serve with Python on board WSGI
def serve(opt={}):
    print "Serving on http://%s:%s" % (opt.host, opt.port)
    from wsgiref.simple_server import make_server
    server = make_server(opt.host, int(opt.port), make_app())
    server.serve_forever()

if __name__ == "__main__":
    class opt:
        host = "127.0.0.1"
        port = 8080
    serve(opt)
