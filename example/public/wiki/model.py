# -*- coding: UTF-8 -*-

import elixir
from elixir import *

import os.path
uri = "sqlite:///" + os.path.dirname(os.path.abspath(__file__)) + "/wiki.sqlite"

elixir.metadata.bind = uri
elixir.metadata.bind.echo = True

class Wiki(Entity):

    title = Field(Unicode(255), primary_key=True)
    body = Field(Unicode)
    created = Field(DateTime)
    updated = Field(DateTime)

    def __repr__(self):
        # return '<Wiki "%s" (%s) #%s>' % (self.title, self.body, self.id)
        return '<Wiki "%s">' % (self.title)

elixir.setup_all(True)

commit = elixir.session.commit

if __name__=="__main__":
    a = Wiki(title="Test", body="Here goes the text")
    print a
    commit()
    print Wiki.query.all()
