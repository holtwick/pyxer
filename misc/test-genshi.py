from pyxer.template.genshi import XML, Stream, QName, Attrs
from pyxer.template.genshi.core import START, END, TEXT
from pyxer.template.genshi.path import Path

#c = Context(a=1)
#print c.a

if 0:
    stream = XML(
        '<html xmlns:py="some">'
        '<p class="intro" py:if="0">Some text and '
        '<a href="http://example.org/">a link</a>.'
        '<br/></p></html>')

    for a in stream:
        print a

    #for output in stream.serialize():
    #    print `output`

    substream = stream.select('//a')
    print substream

    #substream = Stream(list(stream.select('a')))
    #print repr(substream)

    #print stream.render('html')

if 0:
    my = Stream([])
    l = [
        (START, (QName(u'a'), Attrs([(QName(u'href'), u'http://example.org/')])), (None, 1, 63)),
        (TEXT, u'a link', (None, 1, 93)),
        (END, QName(u'a'), (None, 1, 99)),
        (TEXT, u'.', (None, 1, 103)),
        ]

    def do(my):
        for ev in l:
            my.events.append(ev)

    do(my)
    # print "STREAM", repr(my)

    #for x in my:
    #    print "x", x

    print my.select("//a").render("html")

if 1:

    stream = XML(
        '<html xmlns:py="some">'
        '<p class="intro" py:if="0">Some text and '
        ' <a href="http://example.org/">a link</a>.</p>'
        '<p class="intro" py:if="0">Some text and '
        ' <a href="http://example2.org/">a2 link</a>.'
        ' <br/></p></html>')

    #for output in stream.serialize():
    #    print `output`

    match1 = Path('//a').test()
    match2 = Path('//p').test()

    test = match1

    def myFilter(stream):
        depth = 0
        sub = []
        for event in stream:
            if test(event, {}, {}):
                print "Treffer", test
                depth = 1
            if depth>0:
                sub.append(event)
                if event[0] is START:
                    depth += 1
                elif event[0] is END:
                    depth -= 1
                    if depth == 1:
                        print "Ende des Bereiches", sub
                    depth = 0
                    sub = []
            else:
                yield event

    print stream.filter(myFilter).render("xhtml")

    #for event in newstream:
    #    print event
