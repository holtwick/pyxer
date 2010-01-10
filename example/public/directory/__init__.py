# -*- coding: UTF-8 -*-

from pyxer.base import *

import os
import os.path

@controller
def index():
    c.dir = req.params.get("dir", os.path.dirname(__file__))
    if os.path.isdir(c.dir):
        c.parent = os.path.split(c.dir)[0]
        c.files = [(name, os.path.join(c.dir, name), os.path.isdir(os.path.join(c.dir, name))) for name in os.listdir(c.dir)]
    else:
        return "Directory name required"

@controller
def show():
    c.file = req.params.get("file", os.path.dirname(__file__))
    c.code = unicode(open(c.file, "rb").read(), "utf-8")
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename
        from pygments.formatters import HtmlFormatter
        lexer = get_lexer_for_filename(c.file)
        formatter = HtmlFormatter(linenos=True, cssclass="source")
        c.pretty = highlight(c.code, lexer, formatter)
        c.css = HtmlFormatter().get_style_defs('.highlight')
    except:
        log.exception("Pygments failed?")
        c.pretty = None
        c.css = ""
    log.debug("Code: %r", c.css)
