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

log = logging.getLogger(__name__)
here = os.path.dirname(__file__)
base = os.path.join(here, "data")

@expose
def index(x=0):
    return "works! %s" % x

@expose
def default():
    return "Called by default " + request.path