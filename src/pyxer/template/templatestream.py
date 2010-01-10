# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

import cgi
import copy
import inspect
import logging
import os
import os.path
import re
import string
import sys
import types
import re
try:
    import StringIO
except:
    import cStringIO as StringIO

log = logging.getLogger(__name__)

from pyxer.template.genshi import XML, HTML, Stream, QName, Attrs
from pyxer.template.genshi.core import START, END, TEXT, COMMENT, DOCTYPE

# _commands = re.compile(u"\&lt;\%(.*?)\%\&gt;", re.M)
_vars = re.compile(u"""
    \$(
        \$
        |
        \{(.*?)\}
        |
        ([a-z_][a-z_0-9]*)(\.[a-z_][a-z_0-9]*)*
    )
    """, re.M | re.VERBOSE)

class Dict(dict):

    " Helper class to map dicts to attributes "

    def __getattr__(self, name):
        try:
            return dict.__getattr__(self, name)
        except:
            return self[name]

    def __setattr__(self, name, value):
        self[name] = value

class CodeGenerator(object):

    level = 0
    tab = '\t'

    def __init__(self, code = None, level = 0, tab = '\t'):
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

    def end_block(self, nblocks = 1, with_pass = False):
        for n in range(nblocks):
            if with_pass:
                self.line('pass')
            self.level -= 1
            self.pad = self.pad[: - len(self.tab)]

    '''
    def insert_block(self, block):
        lines = block.splitlines()
        if len(lines) == 1:
            # special case single lines
            self.line(lines[0].strip())
        else:
            # adjust the block
            for line in _adjust_python_block(lines, self.tab):
                self.line(line)
    '''

    def __str__(self):
        return '\n'.join(self.code + [''])

    def debug(self):
        for n in range(0, len(self.code)):
            print "%4d:" % (n + 1), self.code[n]

    def pretty(self):
        out = []
        for n in range(0, len(self.code)):
            out.append("%4d: %s" % (n + 1, self.code[n].replace("\t", "    ")))
        return "\n".join(out)

class PyxerStream(Stream):

    def append(self, value):
        self.events.append(value)

    def add(self, value, encoding="utf-8"):
        try:
            if type(value) is types.FunctionType:
                value = value()
            if value is None:
                return
            if isinstance(value, list) or isinstance(value, Stream):
                self.events += list(value)
                return
            if value is True:
                value = '1'
            elif value is False:
                value = '0'
            elif not isinstance(value, unicode):
                value = unicode(str(value), 'utf-8')
            self.events.append((TEXT, value, (None, 0, 0)))
        except Exception, e:
            log.exception("element error")
            self.events.append((TEXT, unicode(e), (None, 0, 0)))

    def inner(self, path):
        result = list(self.select(path))
        if result and result[0][0] == START:
            return result[1:-1]
        return result

    def css(self, selector):
        import pyxer.template.cssselect as select
        path = select.css_to_xpath(selector)
        inner = False
        if selector.endswith(" *"):
            selector = selector[:-2]
            inner = True
        log.debug("CSS Selector %r -> XPath %r (innerHTML %r)", selector, path, inner)
        result = list(self.select(path))
        if inner and result and result[0][0] == START:
            return result[1:-1]
        return result

    selectInner = inner

class TemplateSoup(object):

    """
    Yet another templating system based on BeautyfulSoup
    """

    def __init__(self, source, html5 = False, strict = True, debug = False, xml=False):
        self.strict = strict
        self.html5 = html5
        self.debug = debug
        self.xml = False
        self.code = None
        self.bytecode = None
        self.sourcecode = u""
        self.stream = None
        self.layout = []
        self.extends = []
        self.parse(source)
        self.generateCode()
        self.generateByteCode()

        # Save memory
        if not self.debug:
            self.code = None
            self.sourcecode = None

    def parse(self, source):
        self.source = source

        # Parse source
        if 0: # self.html5:
            import html5lib
            import html5lib.treebuilders
            parser = html5lib.HTMLParser(tree = html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
            self.soup = parser.parse(StringIO.StringIO(self.source))
        else:
            if self.xml:
                self.soup = XML(self.source)
            else:
                self.soup = HTML(self.source)
        return self.soup

    def generateCode(self):
        self.code = CodeGenerator()
        self.code_line = 1

        # Create code
        self.code.line(
            # "# -*- coding: UTF-8 -*-",
            "from pyxer.template.genshi import XML, HTML, Stream, QName, Attrs",
            "from pyxer.template.genshi.core import START, END, TEXT, XML_DECL, DOCTYPE, START_NS, END_NS, START_CDATA, END_CDATA, PI, COMMENT",
            "def _forceUnicode(value):",
                "\tif value is None: return ''",
                "\tif isinstance(value, unicode): return value",
                "\treturn unicode(str(value), 'utf-8')",
            "def select(path):",
                "\tglobal stream",
                "\treturn stream.select(path)"
        )
        self.code.start_block("def main():")
        self.code.line(
            "global stream",
        )

        try:
            self.current_node = self.soup
            self.loop(self.soup)
        except SyntaxError, e:
            #print "###", self.code_line
            #part = self.source.splitlines()[self.code_line: self.code_line+4]
            #print "\n".join(part)
            raise

        self.code.line(
            "return stream"
        )

        self.code.end_block()
        #self.code.line(
        #    "main(soup)",
        #    "print soup",
        #    # "print soup.prettify()",
        #)

        self.sourcecode = unicode(self.code)
        #if self.debug:
        #    print self.code.pretty()

    def generateByteCode(self):
        if self.debug:
            log.debug("Sourcecode:\n%s", self.code.pretty())
        self.bytecode = compile(self.sourcecode, "<string>", "exec")

    def generate(self, __vars__={}, **kw):
        # import pprint

        vars = __vars__
        vars.update(kw)

        # For referencing
        if not vars.has_key("top"):
            vars["top"] = None

        # Prepare context
        context = Dict(vars)
        context.update(
            stream = PyxerStream([])
            )

        # print context.keys()
        stream = None
        try:
            exec(self.bytecode, context)

            stream = context["main"]()
            # pprint.pprint(list(stream))
            context["top"] = stream

            # Applying the layouts
            for layout in self.layout:
                template = eval(layout, context)
                if isinstance(template, TemplateSoup):
                    stream = template.generate(context)

        except:
            # XXX must become more Python conform
            #error = inspect.trace()[-1][0].f_locals.get("error", None)
            #if not error:
            #    raise
            #exc_info = sys.exc_info()
            #e = exc_info[1]
            #if getattr(e, 'args', None):
            #    arg0 = e.args[0]
            #else:
            #    arg0 = str(e)
            #msg = arg0 + "\nError in template line %d: %s" % error
            #raise exc_info[0], msg, exc_info[2]
            raise

        # pprint.pprint(list(stream))

        self.stream = stream
        return stream

    def render(self, method="html", encoding = "utf-8", doctype=None, strip_whitespace=True, **kw):
        method = method.lower()
        if (doctype is None) and (method != 'xml'):
            doctype = 'html'
        if self.stream:            
            return self.stream.render(method,
                strip_whitespace=strip_whitespace,
                doctype=doctype,
                **kw)

    __str__ = render

    def getAttr(self, node, name):
        name = unicode(name)
        value = None
        kind, data, pos = node
        if kind == START:
            attr = data[1]
            # XXX <label for...> problem
            #if not (data[0].lower() == "meta" and name == "content"):
            #    if name in attr:
            #        value = attr.get(name)
            #        node[1] = (data[0], attr - name)
            name = "py:" + name
            if name in attr:
                if value is not None:
                    raise "Attribute %s is defined twice"
                value = attr.get(name)
                node[1] = (data[0], attr - name)
        return value

    def checkSyntax(self, value, mode = "eval"):
        if self.strict:
            try:
                compile(value, "<string>", mode)
            except SyntaxError, msg:
                raise SyntaxError, str(msg) + " in expression %s" % value
        return value

    def addElement(self, kind, data, pos):
        self.code.line("stream.append((%s, %r, %r))" % (kind, data, pos))

    def loop(self, input, depth = 0):

        stack = []
        path = []

        for node in input:

            # Make node changeable
            node = list(node)

            # Split all informations
            kind, data, position = node

            # Set some defaults
            indent = 0
            pyDef = None

            # if in pyContent or pyReplace do not show
            show = not (len(path) and path[-1][2])

            # Handle tags
            if kind == START:

                # Get commands and strip attribute
                pyDef = self.getAttr(node, "def")
                pyMatch = self.getAttr(node, "match")                   # XXX todo
                pyWhen = self.getAttr(node, "when")                     # XXX todo
                pyOtherwise = self.getAttr(node, "otherwise")           # XXX todo
                pyFor = self.getAttr(node, "for")
                pyIf = self.getAttr(node, "if")
                pyChoose = self.getAttr(node, "choose")                 # XXX todo
                pyWith = self.getAttr(node, "with")
                pyReplace = self.getAttr(node, "replace")
                pyContent = self.getAttr(node, "content")
                pyAttrs = self.getAttr(node, "attrs")
                pyStrip = self.getAttr(node, "strip")
                # pyStrip = self.getAttr(node, "select")

                pyExtends = self.getAttr(node, "extends")               # XXX todo
                pyLayout = self.getAttr(node, "layout")

                pyElse = self.getAttr(node, "else")                   # XXX todo
                pyElif = self.getAttr(node, "elif")                   # XXX todo

                # get modified attributes
                attr = node[1][1]

                if pyExtends:
                    self.extends.append(pyExtends)

                if pyLayout:
                    self.layout.append(pyLayout)

                if pyMatch:
                    import uuid
                    pyDef = "match_%s" % uuid.uuid1().hex

                if pyDef:
                    stack.append(self.code)
                    self.code = CodeGenerator()
                    if not pyDef.strip().endswith(")"):
                        pyDef += "()"
                    self.code.start_block("def %s:" % pyDef)
                    self.code.line(
                        "stream = []"
                    )

                #if pyMatch:
                #    self.code.line(
                #        pyMatch
                #    )

                # For error handling
                self.code.line(
                    "error = " + repr(position)
                    )

                if pyFor:
                    self.code.start_block("for %s:" % self.checkSyntax(pyFor))
                    indent += 1

                if pyIf:
                    self.code.start_block("if %s:" % self.checkSyntax(pyIf))
                    indent += 1

                if pyWith:
                    self.code.line(
                        self.checkSyntax(pyWith, "exec"),
                        # pyWith
                    )

                if (pyReplace) or pyStrip:
                    pyStrip = True
                elif show:
                    attrs = []
                    for name, value in attr:
                        pos = 0
                        expr = []
                        for m in _vars.finditer(value):
                            if value[pos:m.start()]:
                                expr.append(repr(unicode(value[pos:m.start()])))
                            cmd = m.group(1)
                            if cmd != "$":
                                if cmd.startswith("{"):
                                    cmd = cmd[1: - 1].strip()
                                expr.append(self.checkSyntax("_forceUnicode(%s)" % cmd))
                            else:
                                expr.append(repr(u"$"))
                                # Escaped dollar $$ -> $
                            pos = m.end()
                        if value[pos:]:
                            expr.append(repr(unicode(value[pos:])))
                        attrs.append("(%r, %s)" % (name, " + ".join(expr) or 'u""'))


                    newattr = "Attrs([%s])" % ", ".join(attrs)
                    if pyAttrs:
                        newattr += " | [(QName(k), _forceUnicode(v)) for k, v in dict(%s).items() if v is not None]" % self.checkSyntax(pyAttrs)

                    element = (START, "(%r, %s)" % (data[0], newattr), position)
                    self.code.line("stream.append((%s, %s, %r))" % element)

                    #self.code.line(
                    #    "node = Tag(soup, %r, [%s], parent)" % (node, ", ".join(attrs)),
                    #    "parent.append(node)",
                    #)

                #if pyFromid:
                #    pyContent = "fromid(%r, top, soup)" % pyFromid

                if pyStrip and pyContent:
                    pyReplace = pyContent
                    pyContent = None

                if pyReplace:
                    self.code.line(
                        "stream.add(%s)" % self.checkSyntax(pyReplace),
                        )

                elif pyContent:
                    self.code.line(
                        "stream.add(%s)" % self.checkSyntax(pyContent),
                        # "print '#', type(value)",
                        # "node.append(value)",
                        )

                # Remember usefull states, pass "whow" settings
                path.append((pyDef, pyStrip, (pyContent or pyReplace or (not show)), indent))

            elif kind == END:

                # Get states from stack
                pyDef, pyStrip, pyContent, indent = path.pop()

                # Recalc show because path is shorter now!
                show = not (len(path) and path[-1][2])

                # print data, pyStrip, indent, show
                if not pyStrip and show:
                    self.addElement(kind, data, position)

                for i in range(indent):
                    self.code.end_block()

                if pyDef:
                    self.code.line(
                        "return stream"
                    )
                    self.code.end_block()
                    lines = self.code.code
                    self.code = stack.pop()
                    self.code.code = lines + self.code.code

            elif kind == TEXT and show:

                # Handle ${...}
                pos = 0
                src = unicode(data)
                for m in _vars.finditer(src):
                    if src[pos:m.start()]:
                        self.addElement(TEXT, unicode(src[pos:m.start()]), position)
                    cmd = m.group(1)
                    if cmd == "$":
                        # Escaped dollar $$ -> $
                        self.addElement(TEXT, u"$", position)
                    else:
                        if cmd.startswith("{"):
                            cmd = cmd[1: - 1].strip()
                        self.code.line(
                            "stream.add(%s)" % self.checkSyntax(cmd),
                        )
                    pos = m.end()
                if src[pos:]:
                    self.addElement(TEXT, unicode(src[pos:]), position)

            elif kind==COMMENT:

                if not data.startswith("!"):
                    self.addElement(kind, data, position)

            elif show:

                # log.debug("Unhandled stream element: %r %r %r", kind, data, position)
                self.addElement(kind, data, position)

Template = TemplateSoup 
HTMLTemplate = TemplateSoup

def testing():

    # ts = TemplateSoup("#$x")
    # print ts.code.pretty()

    # Variables
    value = TemplateSoup("#$x").generate(x=1)
    assert unicode(value) == u"#1"

if __name__ == "__main__":

    if 1:
        level = logging.DEBUG
        try:
            LOG_FORMAT_DEBUG = "%(levelname)s [%(name)s] %(pathname)s line %(lineno)d: %(message)s"
            logging.basicConfig(
                level = level,
                format = LOG_FORMAT_DEBUG)
        except:
            logging.basicConfig()

    log.info("Logging enabled")

    testing()

    if 0:
        def layout(name):
            return TemplateSoup("""
            <html>
                <head>
                    <title  data="$x test">Great!</title>
                </head>
                <body>
                    <div content="top.selectInner('//body')">
                      <h2>Header </h2>
                      <p>Lorem ipsum</p>
                    </div>
                    <hr />
                </body>s
            </html>
            """)

        ts = TemplateSoup("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
            <html layout="layout(123)">
                <body id="test" data="$x $y test">
                    <p>
                        Here we go!
                        <b>Hello</b>
                        $x $y
                        <!-- Comment --> <!--! invisible -->
                        Ende
                </body>
            </html>
            """)
        # print ts.code.pretty()
        ts.generate(dict(x = "äöü", y=str, layout = layout))
        print ts

    if 0:
        t = TemplateSoup("""
        <html xmlns:py="bla">
            <head>
                <title>Great!</title>
            </head>
            <body>
                <a href="/top">Some link</a>
                <div py:def="test">Test</div>
                <hr />
                <b content="test()" />
                <i if="1">Good <i if="0">Bad</i></i>
                <b with="x=123" strip="1">Before $x After</b>
                <b replace="test">Away?</b>
                <em for="y in [1,2,3,2,1]" content="y" />
                <div attrs="{'class': 999}" class="none" />
                <div content="select('//a')" />
            </body>
        </html>
        """)
        print t.generate()

    if 1:
        TEST = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html layout="c.layout">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Python HTML/CSS to PDF converter</title>
</head>
<body>
<p>XXX</p>
<p class="error" py:if="c.error" py:content="c.error">
	ERROR
</p>
<form action="message">
	<p>
		<label for="email">Your email address</label>
		<input type="text" id="email" name="email" value="$c.email">
	</p>
	<p>
		<label for="message">Your message</label>
		<textarea name="message" id="message">$c.message</textarea>
	</p>
	<p>
		<input type="submit" value="Send message to XHTML2PDF">
	</p>
</form>
</body>
</html>
"""

    if 0:
        mod = TemplateSoup(data2, html5 = True)
        mod.code.debug()
        exec(str(mod.code), dict(
            x = 1,
            samples = [
                ("Home", "/"),
                ("Developer", "/developer"),
                ("Contacts", "/legal"),
                ]))

    if 0:
        # t = Template(_test)
        t = Template(_test3, html = True, path = r"c:\test.html")
        print t.source.encode("latin1", "ignore")
        print t.render(dict(name = 'dirk "enzo" holtwick'), encoding = "ascii")


    if 1:
        try:
            ts = TemplateSoup(TEST, debug=1)
            print ts.code.pretty()
            ts.generate(dict(x = "äöü", y=str, layout = layout))
            print ts
        except:
            log.exception("Template")
