# -*- coding: UTF-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2008      ##
## All rights reserved                     ##
#############################################

# import pyxer.helpers as h
# import pyxer.model as model

from webob import exc
# from formencode.htmlfill import render
import sys
import logging
import string
import mimetypes
import imp
import os
import os.path
import types
import urllib
import urlparse

GAE = "google.appengine" in sys.modules

# On stage
if GAE:
    STAGE = (
        os.environ.get('SERVER_SOFTWARE', '').startswith('Google ') or
        os.environ.get('USER', '').startswith('Google ') == 'apphosting')
else:
    STAGE = True
    
stage = STAGE

from pyxer.utils import Dict, AttrDict
from pyxer.utils.jsonhelper import json, json_decode, json_encode
from pyxer.controller import \
    Controller, isController, c, g, h, config, \
    session, response, request, resp, req
from pyxer.routing import Router, static
from pyxer import helpers

import logging
log = logging.getLogger(__name__)

def url(url, *parts, **params):
    " Normalize URL "
    if len(parts):
        url += "/" + "/".join(parts)

    #log.debug("URL (1) %r", url)

    url = urlparse.urljoin(request.environ["pyxer.urlbase"], url)

    log.debug("URL (2) %r", url)

    obj = list(urlparse.urlparse(url))    
    if params:
        query = urllib.urlencode(params)
        # url = request.relative_url(url)
        obj[4] = query

    # If you live behind an Apache proxy
    # XXX Maybe has to go in pyxer.app?
    #if request.environ.has_key("HTTP_X_FORWARDED_HOST"):
    #    log.debug("URL (x) %r %r", obj, request.environ["HTTP_X_FORWARDED_HOST"])
    #    obj[1] = request.environ["HTTP_X_FORWARDED_HOST"]
    #    if not obj[0]:
    #        obj[0] = "http"

    url = urlparse.urlunparse(obj)
    log.debug("URL (3) %r", url)
    return url

def redirect(location=None, permanent=False):
    " Redirect to other page "
    # .exeception for Python 2.3 compatibility
    # 307 
    if location is None:
        location = req.environ["PATH_INFO"]
    if permanent:
        raise exc.HTTPMovedPermanently(location=url(location)).exception
    else:
        raise exc.HTTPSeeOther(location=url(location)).exception

def abort(code=404):
    " Abort with error "
    # .exeception for Python 2.3 compatibility
    raise exc.HTTPNotFound().exception

notfound = abort

_template_cache = {}

class StreamTemplateManager:

    def __init__(self, root):
        self.root = root

    def load(self, path):
        global _template_cache
        import pyxer.template as pyxer_template
        if not stage:
            pyxer_template = reload(pyxer_template)
        path = os.path.abspath(os.path.join(self.root, path))
        # Test if it is in cache and return if found
        mtime = os.path.getmtime(path)
        if stage and _template_cache.has_key(path):
            log.debug("Template fetching from cache")
            template, last = _template_cache.get(path)
            if mtime <= last:
                log.debug("Template fetched from cache")
                return template
            else:
                log.debug("Found a newer file than the one in the cache for %r", path)
        # Load the template
        log.debug("Loading template %r in StreamTemplateManager", path)
        data = file(path, "r").read().lstrip()
        template = pyxer_template.TemplateSoup(
            data,
            xml=data.startswith('<?xml'))
        template.load = self.load
        _template_cache[path] = (template, mtime)
        return template

def template_stream(name=None):
    " Get the template "
    # XXX What to do with dirname? Scenarios?
    # XXX What to do with absolute url /like/this?
    if name is not None:
        path = os.path.join(request.urlvars["pyxer.path"], name)
        dirname = os.path.dirname(path)
    else:
        path = request.template_url
        dirname = os.path.dirname(path)
    log.debug("Loading template %r", path)
    soup_manager = StreamTemplateManager(dirname)
    return soup_manager.load(path)

template = template_default = template_stream

def render_stream(template=None, **kw):
    template = template_stream(name=template)
    template.generate(Dict(c=c, h=Dict(
        url=url,
        redirect=redirect,
        strftime=helpers.strftime,
        stage=STAGE,
        ), load=template.load))
    # logging.info("CT %r", )
    if response.headers['Content-Type'] == 'text/html; charset=utf8':
        response.headers['Content-Type'] = 'text/html; charset=%s' % kw.get("encoding", "utf-8")
    return template.render(**kw)

render_default = render_stream

def render_json(**kw):
    " Render output as JSON object "
    if 'ext' in kw:
        if kw['ext']:
            
            # XXX We need to implement output by extension e.g.
            # file names ending on .json, .yaml, .xml, .rss, .atom
            pass
        
    response.headers['Content-Type'] = 'application/json; charset=%s' % kw.get("encoding", "utf-8")
    result = json(request.result)
    # log.debug("JSON: %r", result)
    return result

def render(result=None, render=None, **kw):
    log.debug("Render called with %r %r %r", repr(result)[:40], render, kw)
    # log.debug("Render called with %r %r", render, kw)

    # log.debug("Response %r %r", response.body_file, response.body)

    # Choose a renderer
    render_func = None

    # Render is explicitly defined by @controller
    if render is not None:
        render_func = render

    # If the result is None (same as no return in function at all)
    # then apply the corresponding template
    # XXX Maybe better test if response.body/body_file is also empty
    elif result is None:
        render_func = render_default

    # Consider dict and list as JSON data
    elif isinstance(result, dict) or isinstance(result, list):
        render_func = render_json

    # Execute render function
    log.debug("Render func %r", render_func)
    if render_func is not None:
        request.result = result
        log.debug("Render with func %r", render_func)
        result = render_func(**kw)

        # Normalize output
        # if (not None) and (not isinstance(result, str)) and (not isinstance(result, str)):
        #    result = str(result)

    # Publish result
    if isinstance(result, unicode):
        response.charset = 'utf-8'
        response.unicode_body = result
    elif isinstance(result, str):
        response.body = result

    return response.body

_render = render

class controller(Controller):

    def render(self, result, render=None, **kw):
        
        if response.body:
            log.debug("Render: Body is already present")
            return response.body
        
        return _render(result, render, **kw)

class expose(controller):

    def call(self, *a, **kw):
        " Add arguments "
        data = {}
        for k, v in dict(request.urlvars).items():
            if not (k.startswith("pyxer.") or k in ("controller", "module")):
                data[k] = v
        request.charset = 'utf8'
        for k,v in request.params.items():
            data[str(k)] = v
        #  data.update(dict(request.params))
        
        # log.debug("Call func with params %r and urlvars %r", dict(request.params), dict(request.urlvars))
        return self.func(**data)

class Permission(object):

    """
    XXX
    
    @controller(permission=Permission('read'))
    """

    def __init__(self, permission):
        self.permission

    def __call__(self, permissions):
        if isinstance(permissions, basestring):
            permissions = [permissions]
        return self.permission in permissions
