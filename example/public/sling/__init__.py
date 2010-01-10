# -*- coding: UTF-8 -*-

from pyxer.base import *
from pyxer.sling import Sling, quote

sling = Sling("127.0.0.1", 7777)

router = Router()
router.add_re("^content/(?P<path>.*?)$", controller="index", name="_content")

@expose
def index(path=None):
    log.debug("Show path %r", path)
    all = sling.getNodes("wiki")
    c.all = [e["jcr:path"].split("/")[-1] for e in all]
    if path:
        c.entry = sling.get("/wiki/" + path)
        c.entry.path = path
        # Get all entries with the correct title
        # result = sling.xpath('wiki/*[@title="%s"]' % xpath_escape(title))
    else:
        # Get first entry
        result = sling.getNodes("wiki", rows=1)
        c.entry = sling.get(result[0])
        c.entry.path = result[0]["jcr:path"].split("/")[-1]
    c.url = url

@expose
def edit(path=None):
    if not path:
        c.entry = dict(
            title = "",
            body = "",
            path = "")
    else:
        c.entry = sling.get("/wiki/" + path)
        c.entry.path = path

@expose
def commit(title, body, path):
    """
    Write form content into database and jump to index page
    to avoid that a reload of the page creates a duplicate entry.
    """
    log.debug("Wiki entry %r %r %r", path, title, body)

    if title:
        if not path:
            path = "*"
        created, path = sling.update("/wiki/" + path, dict(
            title=title,
            body=body,
            created="",
            lastModified="",
            createdBy="",
            lastModifiedBy=""))

        # Redirect to index
        # return '<a href=".">Index</a>'
        redirect(url("content" , path.split("/")[-1]))
    else:
        return "Title is obligatory!"
