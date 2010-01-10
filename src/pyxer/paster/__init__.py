# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from paste import httpserver
from pyxer.app import make_app

#def serve(opt):
#    if opt.reload:
#        import paste.reloader as reloader
#        reloader.install()     
#    httpserver.serve(make_app(), host=opt.host, port=int(opt.port))

import pyxer
import os
import os.path
import sys
from shutil import * 
from pyxer.app import make_app
from pyxer.utils import call_virtual, find_name, find_root, call_script

_paster_ini = """
[app:main]
use = egg:pyxer#main

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = 8080

# Logging configuration
[loggers]
keys = root, app

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = DEBUG
handlers = console

[logger_app]
level = DEBUG
handlers =
qualname = app

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""".lstrip()

_setup_py = """
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name           = "pyxer-project",
    version        = "",
    description    = "",
    license        = "",
    author         = "",
    author_email   = "",    
    keywords       = "pyxer",

    requires       = ["pyxer"],
    packages = find_packages(exclude=['ez_setup']),
        
    include_package_data = True,

    long_description = '',
    classifiers = [x.strip() for x in ''.strip().splitlines()],

    entry_points='''
    [paste.app_factory]
    main = pyxer.app:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    ''',
    )
""".lstrip()

def system(cmd):
    cmd = cmd.strip()
    print "Command:", cmd
    return os.system(cmd)

def setup(opt):
    # Create paster.ini
    if not os.path.isfile("paster.ini"): #opt.update or
        print "create paster.ini"
        open("paster.ini", "w").write(_paster_ini)

def serve(opt, options = [], daemon = ""):
    root = find_root()
    command = "serve"    
    # setup(opt)    
    if daemon: 
        options.append("--daemon")
    if opt.debug:
        options.append("-v")       
    if opt.reload:
        options.append("--reload")   
    ini = os.path.join(root, "development.ini")    
    call_script(["paster", command] + options + [ini, daemon])    

def start(opt):
    serve(opt, options = ["--daemon"])

def stop(opt):
    serve(opt, options = ["--stop-daemon"])

def status(opt):
    serve(opt, options = ["--status"])
