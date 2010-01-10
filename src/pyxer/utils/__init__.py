# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

# import pyxer.utils.jsonhelper
import os
import os.path
import sys
import types
import logging
log = logging.getLogger(__name__)

try:
    import subprocess
except:
    subprocess = None

iswin = (sys.platform == "win32")

class Dict(dict):

    def __getattr__(self, name):
        try:
            return dict.__getattr__(self, name)
        except:
            return self[name]

    def __setattr__(self, name, value):
        self[name] = value

class AttrDict(dict):

    # __slots__ ?

    def __init__(self, dict=None, **kwargs):
        if dict is None:
            dict = kwargs
        for k, v in dict.items():
            self[k] = v

    def __getattr__(self, name):
        try:
            return dict.__getattr__(self, name)
        except:
            return self.get(name, None)

    def __setattr__(self, name, value):
        if (isinstance(value, dict)) and (not isinstance(value, AttrDict)):
            value = AttrDict(value)
        dict.__setitem__(self, name, value)

    def __delattr__(self, name):
        del self[name]

    __setitem__ = __setattr__

    def __getnext__(self, name, full):
        try:
            if "." in name:
                left, right = name.split(".", 1)
                value = self.__getnext__(left, full)
                return value[right]
            else:
                return dict.__getitem__(self, name)
        except:
            raise KeyError, full

    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except:
            return self.__getnext__(name, name)

def html_escape(value):
    return (value
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))

def html_unescape(value):
    return (value
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&lt;", '<')
        .replace("&gt;", '>')
        .replace("&amp;", '&'))

def system(cmd):
    cmd = cmd.strip()
    print "Command:", cmd
    return os.system(cmd)

def find_root(*path):
    cwd = os.getcwd()
    if path:
        cwd = os.path.join(cwd, *path)
    while cwd:
        if os.path.isfile(os.path.join(cwd, "app.yaml")):
            log.debug("Projects root directory is %r", cwd)
            return cwd
        cwd, last = os.path.split(cwd)
        if not last:
            break
    log.warn("Projects root directory could not be found")
    return None

def find_name(root=None):
    if not root:
        root = find_root()
    for name in os.listdir(os.path.join(root, "src")):
        if not name.startswith("."):
            return name
    return None

def call_subprocess(
    command,
    show_stdout=True,
    filter_stdout=None,
    cwd=None,
    extra_env=None):

    if type(command) not  in (types.ListType, types.TupleType):
        raise Exception("List or tuple expected")

    cmd = []
    for part in command:
        if ' ' in part or '\n' in part or '"' in part or "'" in part:
            part = '"%s"' % part.replace('"', '\\"')
        if part:
            cmd.append(part)
    cmd_desc = ' '.join(command)
    if show_stdout:
        stdout = None
    else:
        stdout = subprocess.PIPE
    print ("Running command %s" % cmd_desc)
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
    else:
        env = None
    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            stdin=None,
            stdout=stdout,
            # shell = True,
            cwd=cwd,
            env=env)
    except Exception:
        log.exception("Error while executing command %r", cmd_desc)
        return -1
    all_output = []
    if stdout is not None:
        stdout = proc.stdout
        while 1:
            line = stdout.readline()
            if not line:
                break
            line = line.rstrip()
            all_output.append(line)
            if filter_stdout:
                level = filter_stdout(line)
                if isinstance(level, tuple):
                    level, line = level
                print (level, line)
            else:
                print (line)
    else:
        proc.communicate()
    proc.wait()
    #if env:
    #    os.environ = env
    return proc.returncode

def call_virtual(cmd, root=None, cwd=None):
    if not root:
        root = find_root()
    print "Init virtualenv", root
    if iswin:
        call_subprocess(cmd, extra_env={
            "VIRTUAL_ENV": root,
            "PATH": os.path.join(root, "Scripts") + ";" + os.environ.get("PATH"),
            }, cwd=cwd)
    else:
        call_subprocess(cmd, extra_env={
            "VIRTUAL_ENV": root,
            "PATH": os.path.join(root, "bin") + ";" + os.environ.get("PATH"),
            }, cwd=cwd)

def call_script(cmd, root=None, cwd=None):
    if not root:
        root = find_root()
    if iswin:
        cmd[0] = os.path.join(root, "Scripts", cmd[0] + ".exe")
    else:
        cmd[0] = os.path.join(root, "bin", cmd[0])

    #if cwd is not None:
    #    _cwd = os.getcwd()
    #    os.chdir(cwd)
    #try:

    call_virtual(cmd, root, cwd=cwd)

    #finally:
        #if cwd is not None:
        #    os.chdir(_cwd)

call_bin = call_script

def copy_python(src, dst, symlinks=False):
    " Copies just Python source files "
    import shutil
    names = os.listdir(src)
    try:
        os.makedirs(dst)
    except:
        pass
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                if not name.startswith("."):
                    copy_python(srcname, dstname, symlinks)
            else:
                if name.endswith(".py"):
                    print "create", dstname
                    shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError, why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error, errors

def install_package(here, package, zip=False):
    here = os.path.abspath(here)
    bin = os.path.join(here, '.hidden-bin')
    lib = os.path.join(here, 'site-packages')
    if not os.path.isdir(bin):
        os.makedirs(bin)
    if not os.path.isdir(lib):
        os.makedirs(lib)
    command = ['easy_install-2.5', '-a', '-d', lib, '-s', bin, '-U', package]
    if not zip:
        command.insert(2, '-Z')
    call_subprocess(
        command,
        extra_env={'PYTHONPATH': lib})

def uid():
    import uuid
    return uuid.uuid4().hex

def iso2datetime(isostring):
    import datetime
    import re
    RX_ISOTIME = re.compile("^(\d+)-(\d+)-(\d+)[T ](\d+):(\d+):(\d+)(\.\d+)?")
    m = RX_ISOTIME.search(isostring)
    if m:
        return datetime.datetime(*[(int(v.lstrip('.'))) for v in m.groups() if v is not None])
