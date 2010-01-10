# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

long_description = """
Yet another framework with a new very simple programming concept.
Offers also an own templating language mostly compatible with Genshi.
The command line tool makes creating Google AppEngine projects as easy as possible.
Projects may also be used with Paster or other WSGI frameworks.
Also provides an interface to Apache Sling to access JCR/ Jackrabbit
structures and datas.
""".strip()

setup(
    name = "pyxer",
    version = "VERSION{0.7.3}VERSION"[8: - 8],
    description = "Simple Python Framework and Templating for Paste, Google App Engine (GAE) and WSGI.",
    license = "MIT",
    author = "Dirk Holtwick",
    author_email = "dirk.holtwick@gmail.com",
    url = "http://code.google.com/p/pyxer/",
    download_url = "http://pypi.python.org/pypi/pyxer",
    keywords = "Framework, Google App Engine, GAE, appengine, Paster, Server, Templating, Sling, Jackrabbit, JCR",

    requires = [
        # "webob",
        # "paste",
        ],

    package_dir = {
        '': 'src'
        },

    packages = [
        "pyxer",
        "pyxer.gae",
        "pyxer.paster",
        "pyxer.utils",
        "pyxer.template",
        "pyxer.sling",
        ],

    # packages = find_packages(exclude=['ez_setup']),

    include_package_data = True,

    test_suite = "tests",

    #entry_points = {
    #    'console_scripts': ['pyxer = pyxer.command:command',]
    #    },

    long_description = long_description,

    #classifiers = [x.strip() for x in """
    #    """.strip().splitlines()],

    entry_points = """
[paste.app_factory]
main = pyxer.app:app_factory

[console_scripts]
pyxer = pyxer.command:command
xgae = pyxer.command:command_gae
xpaster = pyxer.command:command_paster
xwsgi = pyxer.command:command_wsgi
""".lstrip(),

    )
