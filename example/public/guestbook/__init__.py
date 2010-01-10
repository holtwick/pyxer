# -*- coding: UTF-8 -*-

from pyxer.base import *

import model

@expose
def index():
    """
    List guest book entries and a form for creating new entries.
    """

    if GAE:

        # Google App Engine
        query = model.GuestBook.all()
        query.order("-date")
        c.messages = query.fetch(limit=20)

    else:

        # Using Elixir
        c.messages = model.Guestbook.query.all()

@expose
def commit(message):
    """
    Write form content into database and jump to index page
    to avoid that a reload of the page creates a duplicate entry.
    """

    if GAE:

        # Google App Engine
        model.GuestBook(message=message).put()

    else:

        # Using Elixir
        model.GuestBook(name, message)
        model.commit()

    # Redirect to index
    redirect(".")
