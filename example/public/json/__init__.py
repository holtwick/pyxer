# -*- coding: UTF-8 -*-

from pyxer.base import *

import math

@controller
def index():
    pass

@controller
def calc():
    try:        
        result = math.sqrt(float(req.params["value"]))
        success = True
    except Exception, e:
        result = str(e)
        success = False
    return dict(
        success = success,
        result = result
        )
