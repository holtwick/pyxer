# -*- coding: UTF-8 -*-

from pyxer.base import *

@controller
def index():
    c.ctr = session.get("ctr", 0)
    session["ctr"] = c.ctr + 1
    session.save()
