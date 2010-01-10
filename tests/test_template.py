# -*- coding: UTF-8 -*-

import unittest
from pyxer.template import *
from pyxer.utils import Dict, AttrDict

import re
import sys

_data = """<!DOCTYPE html>
<html>
 <head>
  <title>TITLE</title>
 </head>
<body>
 BODY
 <br />
</body>
</html>
"""

_sample_begin = """<!DOCTYPE html>
<html>
 <head>
  <title>TITLE</title>
 </head>
<body>
 """

_sample_end = """
</body>
</html>
"""

_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>
            Twittori / $c.screen_name
        </title>
        <link>
            http://www.twittori.com/$c.screen_name
        </link>
        <atom:link type="application/rss+xml" rel="self" href="http://www.twittori.com/$c.screen_name"/>
        <description>
            Twittori updates from XXX.
        </description>
        <language>
            en-us
        </language>
        <ttl>
            40
        </ttl>
        <item py:for="m in c.messages">
            <title py:content='m.text'>
               Titel 
            </title>
            <description py:content='m.text'>
                Description
            </description>
            <pubDate py:content='m.created'>
                Tue, 26 May 2009 17:00:39 +0000
            </pubDate>
            <guid py:content='m.url'>
                http://twitter.com/Volker_Beck/statuses/1925454291
            </guid>
            <link py:content='m.url'>
                http://twitter.com/Volker_Beck/statuses/1925454291
            </link>
        </item>
    </channel>
</rss>
""".lstrip()

class PyxerTemplateTestCase(unittest.TestCase):

    rxbody = re.compile(u"\<body.*?\>(.*)\<\/body\>", re.M|re.DOTALL)

    def stripMeta(self, value):
        """
        Due to a speciality of html5lib just the stuff between <body>...</body>
        without whitespaces seems to be equal to the original source.
        """
        if "<body" in value:
            value = self.rxbody.findall(value)[0]
        return " ".join(value.strip().split())

    def cmpHTML(self, a, b):
        self.assertEqual(self.stripMeta(a), self.stripMeta(b))

    def cmpRender(self, input, output, data={}):
        if "<body" not in input:
            input = _sample_begin + input + _sample_end
        result = HTMLTemplate(input).generate(data).render("xhtml")
        # print HTMLTemplate(input).source.encode("latin1","ignore")
        # print "? %r => %r " % (self.stripMeta(input), self.stripMeta(result))
        self.cmpHTML(output, result)

    def testSample(self):
        # Simple self test without any functionality
        self.cmpRender(_data, _data)

        # Variable
        self.cmpRender(
            "Value $a",
            "Value 999",
            dict(a=999))
        
        # Dotted variables
        c = Dict()
        c.a = Dict()
        c.a.a = 999
        self.cmpRender(
            "Value ${a.a}. And $a.a",
            "Value 999. And 999",
            c)

        # Dotted variables
        c = Dict(v=(1,2,3))        
        self.cmpRender(
            'A <span py:for="x in v" py:strip>$x</span> Z',
            "A 123 Z",
            c)
        
        # Dotted variables
        c = Dict(v=(1,2,3))        
        self.cmpRender(
            'A <span py:for="x in v">$x</span> Z',
            "A <span>1</span><span>2</span><span>3</span> Z",
            c)

    def testXML(self):
        t = Template(_xml, xml=True, debug=False)
        t.generate(Dict(
            c=Dict(
                screen_name='Test',
                messages=[])),
            encoding="ascii")
        r = t.render('xml', doctype=None)
        self.assert_(r.startswith('<?xml'))
        self.assert_('Twittori / Test' in r)

def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
