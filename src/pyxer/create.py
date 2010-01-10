# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

import logging
import os.path
import sys
import shutil
# import pyxer.gae.monkey.boot as boot
import pyxer.utils as utils

log = logging.getLogger(__name__)

from pyxer.utils import call_script, find_root, install_package

INDEX_HTML = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Welcome to Pyxer</title>
</head>
<body>
    <h1>Welcome!</h1>
    <p><strong>Your Pyxer installation is running!</strong></p>
    <p>Continue by adding controllers and files to the &quot;public&quot; directory as described in the documentation.</p>
    <p>Thanks for using Pyxer.</p>
</body>
</html>
""".lstrip()

INIT_PY = """
# -*- coding: UTF-8 -*-

from pyxer.base import *

#@controller
#def index():
#    c.message = "Welcome"
""".lstrip()

ENTRY_POINTS_TXT = """\
[paste.app_factory]
main = pyxer.app:app_factory
"""

APP_YAML = r"""
application: __APP_NAME__
version: 1
runtime: python
api_version: 1
default_expiration: "1d"

handlers:
# *** BEGIN: EXAMPLE CONFIGURATIONS ***
#
#- url: /res/(.*)
#  static_files: public/res/\1
#  upload: public/res/(.*)
#
# *** To make the following work place file in ./res.zip ***
#- url: /res/.*
#  script: $PYTHON_LIB/google/appengine/ext/zipserve
#
#- url: /favicon.ico
#  static_files: public/favicon.ico
#  upload: public/favicon.ico  
#
#- url: /robots.txt
#  static_files: public/robots.txt
#  upload: public/robots.txt     
#
# *** Use this if you want restricted areas for admins ***
#- url: /myamin/.*
#  script: pyxer-app.py
#  login: admin
#
# *** Use this if you want file types to become static ***
#- url: /(.*\.js)
#  static_files: public/\1
#  upload: public/(.*\.js)
#  
# *** END: EXAMPLE CONFIGURATIONS ***
- url: .*
  script: pyxer-app.py

skip_files: |
 ^(
 ((bin|cache|tests|tmp)/.*)|
 (.*/)?(
 (.*\.exe)|
 (.*\.bat)|
 (.*\.pyd)|
 (app\.yaml)|
 (app\.yml)|
 (index\.yaml)|
 (index\.yml)|
 (#.*#)|
 (.*~)|
 (.*\.py[co])|
 (.*\.so)|
 (.*\.dll)|
 (_speedup.*)|
 (.*\.a)|
 (.*\.dll)|
 (.*/RCS/.*)|
 (\..*)
 ))$
""".lstrip() 

PYXERAPP_PY = r'''
# -*- coding: UTF-8 -*-

""" Pyxer on Google App Engine
    http://www.pyxer.net
""" 

import os, sys

# Cleanup the Python path (mainly to circumvent the systems SetupTools)
sys.path = [path for path in sys.path if ("site-packages" not in path) and ('pyxer' not in path)]

# Add our local packages folder to the path
import site
here = os.path.dirname(__file__)
site_lib = os.path.join(here, 'site-packages')
site.addsitedir(site_lib)

# Import the stuff we need to begin serving
from google.appengine.ext.webapp.util import run_wsgi_app
from pyxer.app import make_app

# Set up the WSGI app
def setup_app():
    conf = dict(__file__=os.path.abspath(os.path.join(__file__, os.pardir, 'pyxer.ini')))
    app = make_app(conf)
    
    # Put your custom middleware here e.g.
    # app = MyCoolWSGIMiddleware(app)
    
    return app

# WSGI app remains global
app = setup_app()
    
# The main function is important for GAE to know if the process can be kept in memory
def main():
    run_wsgi_app(app)

# Initialize on first start
if __name__ == "__main__":
    main()
'''.lstrip()


def self_setup(opt, root = None):
    " Set up Pyxer in the virtual environment "
    
    # Find VM
    if not root:
        root = find_root()    
    if not root:
        raise Error, "VirtualENV not found"
    here = os.path.dirname(__file__) 
    
    # Find site_packages folder
    site_packages = os.path.join(root, 'site-packages')
    
    # If the directory does not exist we need to install the basic stuff    
    if not os.path.isdir(site_packages):
        install_package(root, 'paste')
        install_package(root, 'setuptools')
        install_package(root, 'beaker')
    
    # Remove old installation 
    pyxer_dir = os.path.join(site_packages, "pyxer")
    if os.path.isdir(pyxer_dir):
        log.info("Remove Pyxer directory %r", pyxer_dir)
        pass
    
    # Copy package
    log.info("Copy from %r to %r", here, pyxer_dir)
    utils.copy_python(here, pyxer_dir)

    # This is needed for the paster app
    egg_dir = os.path.join(site_packages, "pyxer.egg-info")
    if not os.path.isdir(egg_dir):
        os.makedirs(egg_dir)
    open(os.path.join(egg_dir, "entry_points.txt"), "w").write(ENTRY_POINTS_TXT)

    # Create pyxer-app.py
    pyxer_starter = os.path.join(root, 'pyxer-app.py')
    if opt.force or (not os.path.isfile(pyxer_starter)):
        log.info("Create %r", pyxer_starter)
        open(pyxer_starter, "w").write(PYXERAPP_PY)
            
def create(opt, here):

    import codecs
    
    # Change to AppEngine module replacements
    # os.chdir(os.path.join(os.path.dirname(monkey.__file__), "monkey"))

    # Create directory
    if not os.path.exists(here):
        os.makedirs(here)

    # Create gae.ini
    app_name = []
    app_yaml_path = os.path.join(here, "app.yaml")
    if not os.path.exists(app_yaml_path):
        # name = raw_input("Name of project: ")
        name = 'unnamed'
        open(app_yaml_path, "w").write(APP_YAML.replace('__APP_NAME__', name).encode('ascii'))

    # Create public dir
    path = os.path.join(here, "public")
    if not os.path.exists(path):
        os.makedirs(path)
        codecs.open(os.path.join(path, "index.html"), "w", 'utf-8').write(INDEX_HTML.encode("utf-8"))
        codecs.open(os.path.join(path, "__init__.py"), "w", 'utf-8').write(INIT_PY.encode("utf-8"))        

    # Install pyxer
    self_setup(opt, here)

    print "Initialization completed!"
