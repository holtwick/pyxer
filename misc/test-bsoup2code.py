# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

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

    Wert $x

    <p py:if="x==1">X1 Und noch was Text</p>
    <p py:if="x!=1">X0 Und noch was Text</p>

    $${title}

    <div py:content="HTML('<b >nono</b  >')" py:strip="1"> leer </div>
    <div py:content="HTML('<b >nono</b  >')"> leer </div>
    <div py:replace="1+2"> leer </div>

    <div py:attrs="{'class': 'name', 'id': 123+}" />

    <li py:for="name, link in samples">
        <a href="$link">$name</a>
    </li>

</html>
"""

from BeautifulSoup import *
import StringIO
import re

import logging
log = logging.getLogger(__name__)

# _commands = re.compile(u"\&lt;\%(.*?)\%\&gt;", re.M)
_vars = re.compile(u"""
    \$(
        \$
        |
        \{(.*?)\}
        |
        ([a-z_][a-z_0-9]*)(\.[a-z_][a-z_0-9]*)*
    )
    """, re.M|re.VERBOSE)

class CodeGenerator(object):

    level = 0
    tab = '\t'

    def __init__(self, code=None, level=0, tab='\t'):
        self.code = code or []
        if level != self.level:
            self.level = level
        if tab != self.tab:
            self.tab = tab
        self.pad = self.tab * self.level

    def line(self, *lines):
        for text in lines:
            self.code.append(self.pad + text)

    def start_block(self, text):
        self.line(text)
        self.level += 1
        self.pad += self.tab

    def end_block(self, nblocks=1, with_pass=False):
        for n in range(nblocks):
            if with_pass:
                self.line('pass')
            self.level -= 1
            self.pad = self.pad[:-len(self.tab)]

    def insert_block(self, block):
        lines = block.splitlines()
        if len(lines) == 1:
            # special case single lines
            self.line(lines[0].strip())
        else:
            # adjust the block
            for line in _adjust_python_block(lines, self.tab):
                self.line(line)

    def __str__(self):
        return '\n'.join(self.code + [''])

    def debug(self):
        for n in range(0, len(self.code)):
            print "%4d:" % (n+1), self.code[n]

# tree = etree.parse(input, PyxerTreeBuilder())
#for node in tree:
#    print "#", len(node)

class ModuleGenerator(object):

    def __init__(self, source, html5=False, strict=True):
        self.source = source
        self.code = CodeGenerator()
        self.code_line = 1
        self.strict = strict

        # Parse source
        if html5:
            import html5lib
            import html5lib.treebuilders
            parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
            self.soup = parser.parse(StringIO.StringIO(self.source))
        else:
            self.soup = BeautifulSoup(self.source)

        # Create code
        self.code.line(
            "from BeautifulSoup import *",
            "soup = BeautifulSoup()",
        )
        self.code.start_block("def main(soup):")
        self.code.line(
            "parent = soup",
        )

        try:
            self.current_node = self.soup
            self.loop(self.soup)
        except SyntaxError, e:
            #print "###", self.code_line
            #part = self.source.splitlines()[self.code_line: self.code_line+4]
            #print "\n".join(part)
            raise
        self.code.end_block()
        self.code.line(
            "main(soup)",
            "print soup",
            # "print soup.prettify()",
        )

    def getAttr(self, node, name):
        value = None
        if node.has_key("py:" + name):
            value = node["py:" + name]
            del node["py:" + name]
        #if node.attrib.has_key("{http://pyxer.org/ns}" + name):
        #    if value is not None:
        #        raise "Attribute %s is defined twice"
        #    value = node.attrib.pop("{http://pyxer.org/ns}" + name)
        #if node.attrib.has_key("py:" + name):
        #    if value is not None:
        #        raise "Attribute %s is defined twice"
        #    value = node.attrib.pop("py:" + name)
        #if node.attrib.has_key(name):
        #    if value is not None:
        #        raise "Attribute %s is defined twice"
        #    value = node.attrib.pop(name)
        return value

    def checkSyntax(self, value):
        # XXX todo
        if self.strict:
            compile(value, "<string>", "eval")
        return value

    def loop(self, nodes, depth=0):
        for node in nodes:
            indent = 0

            # Handle tags
            if isinstance(node, Tag):

                pyDef = self.getAttr(node, "def")
                pyMatch = self.getAttr(node, "match")
                # pyWhen = self.getAttr(node, "when")
                # pyOtherwise = self.getAttr(node, "otherwise")
                pyFor = self.getAttr(node, "for")
                pyIf = self.getAttr(node, "if")
                pyChoose = self.getAttr(node, "choose")
                pyWith = self.getAttr(node, "with")
                pyReplace = self.getAttr(node, "replace")
                pyContent = self.getAttr(node, "content")
                pyAttrs = self.getAttr(node, "attrs")
                pyStrip = self.getAttr(node, "strip")

                pyExtends = self.getAttr(node, "extends")
                pyLayout = self.getAttr(node, "layout")

                if pyFor:
                    self.code.start_block("for %s:" % self.checkSyntax(pyFor))
                    indent += 1

                if pyIf:
                    self.code.start_block("if %s:" % self.checkSyntax(pyIf))
                    indent += 1

                if pyReplace or pyStrip:
                    pyStrip = True
                else:
                    self.code.line(
                        "line = %d" % self.code_line,
                        "node = Tag(soup, %r, %r)" % (node.name, node.attrs),
                        "parent.append(node)",
                    )

                if pyStrip and pyContent:
                    pyReplace = pyContent
                    pyContent = None

                if pyReplace:
                    self.code.line(
                        "value = element(%s)" % self.checkSyntax(pyReplace),
                        "print '#', type(value)",
                        "parent.append(value)",
                        )

                elif pyContent:
                    self.code.line(
                        "value = element(%s)" % self.checkSyntax(pyContent),
                        "print '#', type(value)",
                        "node.append(value)",
                        )

                if pyAttrs and not pyStrip:
                    self.code.line(
                        "attrs = %s" % self.checkSyntax(pyAttrs),
                        "for key, value in attrs.items(): node[key] = unicode(value)",
                        )

                # print " " * depth, "<%s> %s" % (node.name, node.attrs)

            # Handle the rest
            elif isinstance(node, NavigableString):

                # Count line numbers for error reporting
                self.code_line += unicode(node).count(u'\n')

                if isinstance(node, ProcessingInstruction):
                    pass
                elif isinstance(node, Declaration):
                    self.code.line(
                        "node = Declaration(%r)" % NavigableString.__str__(node),
                        "parent.append(node)",
                    )
                elif isinstance(node, CData):
                    self.code.line(
                        "node = CData(%r)" % NavigableString.__str__(node),
                        "parent.append(node)",
                    )
                elif isinstance(node, Comment):
                    self.code.line(
                        "node = Comment(%r)" % NavigableString.__str__(node),
                        "parent.append(node)",
                    )
                else:

                    # Handle ${...}
                    pos = 0
                    src = unicode(node)
                    for m in _vars.finditer(src):
                        cmd = m.group(1)
                        if cmd != "$":
                            if cmd.startswith("{"):
                                cmd = cmd[1:-1].strip()
                            if src[pos:m.start()]:
                                self.code.line(
                                    "node = NavigableString(%r)" % unicode(src[pos:m.start()]),
                                    "parent.append(node)",
                                )
                            self.code.line(
                                "value = element(%s)" % self.checkSyntax(cmd),
                                # "node = NavigableString(value)",
                                "parent.append(value)",
                            )
                        else:
                            # Escaped dollar $$ -> $
                            self.code.line(
                                "node = NavigableString(%r)" % u"$",
                                "parent.append(node)",
                            )
                        pos = m.end()
                    if src[pos:]:
                        self.code.line(
                            "node = NavigableString(%r)" % unicode(src[pos:]),
                            "parent.append(node)",
                        )

            # This must be an error!
            else:
                # print "XXX", type(node), repr(node)
                raise "Unknown element"

            # Next level
            if hasattr(node, "contents") and not(pyContent or pyReplace or pyStrip):
                self.code.line(
                    "parent = node",
                )
                self.loop(node, depth + 1)
                self.code.line(
                    "parent = parent.parent",
                )

            for i in range(indent):
                self.code.end_block()

def element(value):
    try:
        if type(value) is types.FunctionType:
            value = value()
        if value is None:
            return NavigableString(u'')
        if isinstance(value, Tag):
            return value
        return NavigableString(unicode(value))
    except Exception, e:
        log.exception("element error")
        return NavigableString(unicode(e))
    return NavigableString(u'')

if __name__=="__main__":
    # mod = ModuleGenerator(data)
    mod = ModuleGenerator(data2, html5=True)
    mod.code.debug()
    exec(str(mod.code), dict(
        element=element,
        HTML=BeautifulSoup,
        XML=BeautifulSoup,
        x=1,
        samples=[
            ("Home", "/"),
            ("Developer", "/developer"),
            ("Contacts", "/legal"),
            ]))
