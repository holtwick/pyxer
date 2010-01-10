# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from pyxer.base import *

import sys
import os
import logging
import pyxer
import pprint

log = logging.getLogger(__name__)
here = os.path.dirname(__file__)
base = os.path.join(here, "data")

db = None

def __init__(app):
    app.register("wiki/(.*?).html", index)
    print "Startup", db, here
    db = "Test"

def __del__(app):
    print "Shutdown", db, here
    db = None

@controller
def index():
    c.isgae = "google.appengine" in sys.modules
    c.ispaster = not c.isgae
    c.pyxerversion = pyxer.__version__
    c.modules = sys.modules
    c.platform = sys.platform
    c.samples = []
    c.env = pprint.pformat(os.environ)
    for name in sorted(os.listdir(here)):
        try:
            readme = os.path.join(here, name, "README-GAE.txt")
            if os.path.isfile(readme):
                f = open(readme, "r")
                c.samples.append((
                    f.readline().strip(),
                    name + "/",
                    f.read().strip()))
                f.close()
                log.debug("Added sample %r", c.samples[ - 1])
        except:
            log.exception("Error while collecting samples")
