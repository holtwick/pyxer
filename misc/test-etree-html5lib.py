# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

#try:
#    import xml.etree.cElementTree as etree
#except:
import xml.etree.ElementTree as etree
import StringIO

# ns_py = etree.QName('http://namespace/uri', 'py')

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

class PyxerTreeBuilder(etree.XMLTreeBuilder):

    def doctype(self, name, pubid, system):
        print "***", name, pubid, system


import html5lib
from html5lib import treebuilders, serializer, treewalkers
from html5lib.filters import sanitizer
from html5lib.constants import voidElements

input = StringIO.StringIO(data)
parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("etree", implementation=etree))
tree = parser.parse(input)
# tree = etree.parse(input, PyxerTreeBuilder())

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
