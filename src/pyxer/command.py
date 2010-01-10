# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

from optparse import OptionParser
from pyxer.utils import system, call_subprocess, find_root, install_package
from pyxer import VERSION_STR

import logging
import sys
import os
import os.path

try:
    log = logging.getLogger(__name__)
except:
    log = logging.getLogger(__file__)

_description = """
Yet another Python framework
""".strip()

def showlog(debug):
    level = logging.WARN
    if debug:
        level = logging.DEBUG
    try:
        LOG_FORMAT_DEBUG = "%(levelname)s [%(name)s] %(pathname)s line %(lineno)d: %(message)s"
        logging.basicConfig(
            level = level,
            format = LOG_FORMAT_DEBUG)
    except:
        logging.basicConfig()

class OptParser(OptionParser):

    def print_help(self):
        OptionParser.print_help(self)
        # parser.print_usage()
        # print parser.format_option_help()
        print
        print """
Commands:
  init               Create a new project
  serve              Serves the project
  push               Upload project to GAE 
  push_empty         Upload empty project with version'0' to GAE
  update             Update local pyxer package
  install            Install or update local Python package 
  zipinstall         Install or update local Python ZIP package (slow on GAE)

Daemon commands (only paster):
  start              Start
  stop               Stop
  status             Status
  reload, restart    Restart
""".strip()

    #def error(self, msg):
    #    OptionParser.error(self, msg)
    #    print "Use option --help for complete help"

iswin = (sys.platform == "win32")

def command(engine = None):

    parser = OptParser(
        # "usage: %prog [options] command",
        "Usage: pyxer [options] command",
        description = _description,
        version = VERSION_STR,
        # epilog="Neu\n\r\n" + 20*"hallo ",
        )

    parser.add_option(
        "-q",
        "--quiet",
        action = "store_false",
        dest = "verbose",
        default = True,
        help = "Do not print status messages to stdout")
    #parser.add_option(
    #    "-f",
    #    "--force",
    #    action="store_false",
    #    dest="force",
    #    default=True,
    #    help="don't print status messages to stdout")
    parser.add_option(
        "-d",
        "--debug",
        action = "store_true",
        dest = "debug",
        default = False,
        help = "Activate debug logging")
    if not engine:
        parser.add_option(
            "--engine",
            dest = "engine",
            default = "",
            help = "Engine that will be used: gae (default), wsgi, paster")
    parser.add_option(
        "--port",
        dest = "port",
        default = "8080",
        help = "serving on port")
    parser.add_option(
        "--host",
        dest = "host",
        default = "0.0.0.0",
        help = "Serving on host")
    parser.add_option(
        "-r",
        "--reload",
        dest = "reload",
        action = "store_true",
        help = "Reload on changing files")
    #parser.add_option(
    #    "-u",
    #    "--update",
    #    dest = "update",
    #    action = "store_true",
    #    help = "update suplementary data and files")
    parser.add_option(
        "-U",
        "--develop",
        dest = "develop",
        action = "store_true",
        help = "Update projects Pyxer version")
    parser.add_option(
        "-c",
        "--clear",
        dest = "clear",
        action = "store_true",
        help = "Empty local GAE datastore")
    parser.add_option(
        "-f",
        "--force",
        dest = "force",
        action = "store_true",
        help = "Force updates; overwrites pyxer-app.py")    
    (opt, args) = parser.parse_args()

    showlog(opt.debug)

    #config_default = {
    #    "pyxer.debug":              (cBOOL, False),
    #    "pyxer.sessions":           (cBOOL, False),
    #    "pyxer.engine":             (cSTRING, ""),
    #    "pyxer.templating":         (cSTRING, ""),
    #    "pyxer.host":               (cSTRING, "127.0.0.1"),
    #    "pyxer.port":               (cINT, 8080, 0, 65536),
    #    }

    if (len(args) < 1) or (len(args) > 2):
        log.debug("Minimum 1 argument, maximum 2")
        parser.print_help()
        # parser.error("incorrect number of arguments")
        sys.exit(1)

    command = args[0].lower()

    # Directory argument
    if len(args) == 2:
        here = os.path.abspath(args[1])
    else:
        here = os.getcwd()

    # Get engine
    if engine:
        opt.engine = engine

    log.debug("Command %r for engine %r in directory %r", command, engine, here)

    if opt.engine in ("paster", "paste", "p"):
        print "Paster"
        opt.engine = "paster"
        import pyxer.paster as engine
    elif opt.engine in ("wsgi", "w"):
        print "Python WSGI"
        engine = None
    else:
        print "Google AppEngine"
        opt.engine = "gae"
        import pyxer.gae as engine
        
    # Update version
    if opt.develop and command not in ("setup", "create", "init", "pyxer"):
        import pyxer.create
        pyxer.create.self_setup(opt)

    # Serve
    if command == "serve":
        if engine:
            engine.serve(opt)
        else:
            if opt.debug:
                logging.basicConfig(level = logging.DEBUG)
            import pyxer.app
            pyxer.app.serve(opt)

    # Setup
    elif (command in ("setup", "create", "init")):
        import pyxer.create
        pyxer.create.create(opt, here)

    # Install
    elif (command in ("install")):
        if len(args)==2:
            install_package(os.getcwd(), args[1])

    # ZIP Install
    elif (command in ("zipinstall")):
        if len(args)==2:
            install_package(os.getcwd(), args[1], zip=True)

    # Activate
#    elif (command in ("open", "activate", "vm")):
#
#        root = find_root()
#        if not root:
#            print "No project found"
#        elif iswin:
#            # call_subprocess([os.path.join(root, "scripts", "activate.bat")])
#            system("start " + os.path.join(root, "scripts", "activate.bat"))
#        else:
#            print "IMPORTANT! Leave VM with command 'exit'."
#            call_subprocess(["bash", "--init-file", os.path.join(root, "bin", "activate")], raise_on_returncode = False)
            
    # Deactivate
#    elif (command == "close" or command == "deactivate"):
#
#        root = find_root()
#        if not root:
#            print "No project found"
#        elif iswin:
#            system(os.path.join(root, "scripts", "deactivate.bat"))
#        else:
#            pass

    # Daemon
    elif command == "start" and opt.engine == "paster":
        engine.serve(opt, daemon = "start")
    elif command == "stop" and opt.engine == "paster":
        engine.serve(opt, daemon = "stop")
    elif command == "status" and opt.engine == "paster":
        engine.serve(opt, daemon = "status")
    elif (command in ("reload", "restart")) and opt.engine == "paster":
        engine.serve(opt, daemon = "restart")

    # GAE Upload
    elif (command in ("upload", "deploy", "push")) and opt.engine == "gae":
        engine.upload(opt)
    # GAE empty
    elif (command in ("push_empty")) and opt.engine == "gae":
        if len(args)==2:
            name =  args[1]
            import tempfile
            tmpdir = tempfile.mkdtemp()
            print "Empty project", name , "created at", tmpdir
            tmpfle = os.path.join(tmpdir, 'app.yaml')
            open(tmpfle, 'w').write("""
application: %s
version: 0
runtime: python
api_version: 1

handlers:
- url: /
  static_dir: empty            
            """.strip() % name)
            engine.upload(opt, root=tmpdir)
            os.remove(tmpfle)
            os.rmdir(tmpdir)
            print
            print "ATTENTION: Go to GAE dasboard/versions and switch to version '0' to turn off your project"
        else:
            print '*** Project name needed as last argument'
            
    # GAE fix
    #elif (command == "fix" or command == "fixup") and opt.engine == "gae":
    #    engine.fix()

    # Setup Pyxer
    elif command in ("pyxer", "update", "up"):        
        import pyxer.create
        pyxer.create.self_setup(opt)
        
    else:
        parser.print_help()
        sys.exit(1)
        # parser.error("unsupported command")

    # print options, args

def command_gae():
    command("gae")

def command_paster():
    command("paster")

def command_wsgi():
    command("wsgi")
        
if __name__=="__main__":
    command()
