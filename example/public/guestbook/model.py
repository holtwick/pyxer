# -*- coding: UTF-8 -*-

from pyxer.base import *

if GAE:

    from google.appengine.ext import db
    from google.appengine.api import users

    class GuestBook(db.Model):
        message = db.StringProperty()
        date = db.DateTimeProperty(auto_now_add=True)

else:

    import elixir
    from elixir import Entity, Field, Unicode, session

    import os.path
    uri = "sqlite:///" + os.path.dirname(os.path.abspath(__file__)) + "/guestbook.sqlite"

    elixir.metadata.bind = uri
    elixir.metadata.bind.echo = True

    class GuestBook(Entity):
        message = Field(Unicode)
        # date = Field(Unicode)

    elixir.setup_all(True)
    commit = elixir.session.commit

    if __name__=="__main__":
        a = Wiki(title="Test", body="Here goes the text")
        print a
        commit()
        print Wiki.query.all()
