# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from pyxer.base import *

import logging
log = logging.getLogger(__name__)

@controller
def index():
    # The most simple error ;)
    x = 1/0
