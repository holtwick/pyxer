# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

data = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html py:extends="load('layout.html')" xmlns:py="http://purl.org/kid/ns#">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Home</title>
<script type="text/javascript">
    <!--
        if(i>2) alert(1)
    // -->
    </script>
</head>
<body>
<h1>Pyxer Examples</h1>
<p>
	You are running
    <a href="http://code.google.com/p/pyxer/">Pyxer ${c.pyxerversion}</a>
    on
	<a py:if="c.ispaster" href="http://pythonpaste.org/">Paster</a>
	<a py:if="c.isgae" href="http://code.google.com/appengine/">Google App Engine</a>
  </p>
<ul>
  <li py:for="name, link, description in c.samples">
    <a href="$link">$name</a>
    <div py:if="description">
        $description
    </div>
  </li>
</ul>
 {{ x=1 }}
<!--!
<p>All modules</p>
<ul>
  <li py:for="m in sorted(c.modules)">$m</li>
</ul>
--><?python
title = "The Mandelbrot Set"
def color(x,y):
    z = c = complex(x, -y)/100.0
    for n in range(16):
        z = z*z + c
        if abs(z) > 2:
            break
    return "#%x82040" % n
?>

</body>
</html>
"""

data2 = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
    <script type="text/javascript">
    <!--
        if(i>2) alert(1)
    // -->
    </script>
</head>
<body>
    <h1>Start</h1>

    <% def test(a): %>

        <p>Hier wohnt $a.</p>

        <% return "Nix" %>

    <% end %>

    <% x=1; y='ה' %>

    <% if name: %>

        <% for i in range(1,5): %>

            $i Hello ${name.capitalize()} $x$y <br />

            <% print 2*3 %>

        <% end %>

    <% else: %>

        What's your name? הצü

    <% end %>

    ${test('Anna')}
    <% test('Jupp') %>

    <h1 py:def="title" py:strip class="py_$name">Title</h1>

    <p id="content">
        Some <b>Content</b>
    </p>

    ${id_content}

    <!--! Weg -->
    <? Was? ?>
    <br>

    <p py:if="x==1">X1 Und noch was Text</p>
    <p py:if="x!=1">X0 Und noch was Text</p>

    $${title}

</html>
"""

import html5lib
from html5lib import treebuilders, serializer, treewalkers
from html5lib.filters import sanitizer
from html5lib.constants import voidElements

from BeautifulSoup import *
import StringIO

if 0:
    input = StringIO.StringIO(data)
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    tree = parser.parse(input)
else:
    tree = BeautifulSoup(data)


# tree = etree.parse(input, PyxerTreeBuilder())
#for node in tree:
#    print "#", len(node)

def loop(tree, nodes, depth=0):
    for node in nodes:
        if isinstance(node, Tag) and node.contents:
            print " " * depth, "<%s> %s" % (node.name, node.attrs)
        elif isinstance(node, ProcessingInstruction):
            # print " " * depth, "<?", repr(node[:40])
            pass
        elif isinstance(node, Declaration):
            print " " * depth, "<!DOCTYPE", repr(node[:40])
        elif isinstance(node, CData):
            print " " * depth, "<!CDATA", repr(node[:40])
        elif isinstance(node, Comment):
            print " " * depth, "<!--", repr(node[:40])
        elif isinstance(node, NavigableString):
            print " " * depth, repr(node[:40]), type(node)
        else:
            print " " * depth, type(node)

        if hasattr(element, "contents"):
            loop(tree, node, depth + 1)

            '''
            pyIf = getAttr(node, "if")
            pyFor = getAttr(node, "for")
            pyExtends = getAttr(node, "extends")
            if node.tag == "html" and node.attrib.has_key("xmlns:py"):
                del node.attrib["xmlns:py"]
            if pyFor:
                print "***", pos
                element.insert(pos+1, etree.Element("x"))
                element.insert(pos+1, etree.Element("x"))
                # element.insert(pos+2, node.copy())
                pos += 2

        #    print ">>>", pyIf
        print "_"*depth, node.tag, node.items(), repr(node.text), repr(node.tail)
        if len(node):
            loop(tree, node, depth+1)
        pos += 1
        '''

loop(tree, tree)

'''
def getAttr(node, name):
    value = None
    if node.attrib.has_key("{http://purl.org/kid/ns#}" + name):
        value = node.attrib.pop("{http://purl.org/kid/ns#}" + name)
    if node.attrib.has_key("{http://pyxer.org/ns}" + name):
        if value is not None:
            raise "Attribute %s is defined twice"
        value = node.attrib.pop("{http://pyxer.org/ns}" + name)
    if node.attrib.has_key("py:" + name):
        if value is not None:
            raise "Attribute %s is defined twice"
        value = node.attrib.pop("py:" + name)
    if node.attrib.has_key(name):
        if value is not None:
            raise "Attribute %s is defined twice"
        value = node.attrib.pop(name)
    return value

def loop(tree, element, depth=0):
    pos = 0
    for node in element:
        if etree.iselement(node):
            pyIf = getAttr(node, "if")
            pyFor = getAttr(node, "for")
            pyExtends = getAttr(node, "extends")
            if node.tag == "html" and node.attrib.has_key("xmlns:py"):
                del node.attrib["xmlns:py"]
            if pyFor:
                print "***", pos
                element.insert(pos+1, etree.Element("x"))
                element.insert(pos+1, etree.Element("x"))
                # element.insert(pos+2, node.copy())
                pos += 2

        #    print ">>>", pyIf
        print "_"*depth, node.tag, node.items(), repr(node.text), repr(node.tail)
        if len(node):
            loop(tree, node, depth+1)
        pos += 1

loop(tree, tree)
# print dir(tree)
etree.dump(tree)
'''
