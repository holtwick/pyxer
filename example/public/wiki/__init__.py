# -*- coding: UTF-8 -*-

from pyxer.base import *
from sqlalchemy import desc

import model
import datetime

log = logging.getLogger(__name__)

router = Router()
router.add("^content\/(?P<title>.*?)$", controller="index", name="_content")

@expose
def index(title=""):
    # Get data from databaseel
    result = None
    if title:
        result = model.Wiki.query.filter_by(title=title).order_by(desc(model.Wiki.created)).one()
    if not result:
        # Default values
        result = dict(
            title = "First Page",
            body = "Enter your content here"
            )
    log.debug("Query: %r", result)
    c.entry = result

@expose
def commit(title, body):
    """
    Write form content into database and jump to index page
    to avoid that a reload of the page creates a duplicate entry.
    """

    log.debug("Wiki entry %r %r", title, body)

    # Using Elixir
    try:
        entry = model.Wiki.query.filter_by(title=title).order_by(desc(model.Wiki.created)).one()
    except:
        entry = model.Wiki()
    entry.title = title
    entry.body = body
    model.commit()

    # Redirect to index
    redirect(".")
