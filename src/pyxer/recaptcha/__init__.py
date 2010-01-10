from pyxer.base import *

if GAE:
    import urllib
    from google.appengine.api import urlfetch
else:
    import urllib2, urllib

"""
    Adapted from http://pypi.python.org/pypi/recaptcha-client
    to use with Google App Engine
    by Joscha Feth <joscha@feth.com>
    Version 0.1
"""

API_SSL_SERVER  ="https://api-secure.recaptcha.net"
API_SERVER      ="http://api.recaptcha.net"
VERIFY_SERVER   ="api-verify.recaptcha.net"

class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid = is_valid
        self.error_code = error_code

def displayhtml (public_key,
                 use_ssl = False,
                 error = None):
    """Gets the HTML to display for reCAPTCHA

    public_key -- The public api key
    use_ssl -- Should the request be sent over ssl?
    error -- An error message to display (from RecaptchaResponse.error_code)"""

    error_param = ''
    if error:
        error_param = '&error=%s' % error

    if use_ssl:
        server = API_SSL_SERVER
    else:
        server = API_SERVER

    return """<script type="text/javascript" src="%(ApiServer)s/challenge?k=%(PublicKey)s%(ErrorParam)s"></script>

<noscript>
  <iframe src="%(ApiServer)s/noscript?k=%(PublicKey)s%(ErrorParam)s" height="300" width="500" frameborder="0"></iframe><br />
  <textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
  <input type='hidden' name='recaptcha_response_field' value='manual_challenge' />
</noscript>
""" % {
        'ApiServer' : server,
        'PublicKey' : public_key,
        'ErrorParam' : error_param,
        }

def submit (recaptcha_challenge_field,
            recaptcha_response_field,
            private_key,
            remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field from the form
    recaptcha_response_field -- The value of recaptcha_response_field from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len (recaptcha_response_field) and len (recaptcha_challenge_field)):
        return RecaptchaResponse (is_valid = False, error_code = 'incorrect-captcha-sol')


    def encode_if_necessary(s):
        if isinstance(s, unicode):
            return s.encode('utf-8')
        return s

    params = urllib.urlencode ({
            'privatekey': encode_if_necessary(private_key),
            'remoteip' :  encode_if_necessary(remoteip),
            'challenge':  encode_if_necessary(recaptcha_challenge_field),
            'response' :  encode_if_necessary(recaptcha_response_field),
            })

    request = urllib2.Request (
        url = "http://%s/verify" % VERIFY_SERVER,
        data = params,
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Python"
            }
        )

    httpresp = urllib2.urlopen (request)

    return_values = httpresp.read ().splitlines ();
    httpresp.close();

    return_code = return_values [0]

    if (return_code == "true"):
        return RecaptchaResponse (is_valid=True)
    else:
        return RecaptchaResponse (is_valid=False, error_code = return_values [1])

def submit_gae (recaptcha_challenge_field,
            recaptcha_response_field,
            private_key,
            remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field from the form
    recaptcha_response_field -- The value of recaptcha_response_field from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len (recaptcha_response_field) and len (recaptcha_challenge_field)):
        return RecaptchaResponse (is_valid = False, error_code = 'incorrect-captcha-sol')

    headers = {
               'Content-type':  'application/x-www-form-urlencoded',
               "User-agent"  :  "reCAPTCHA GAE Python"
               }

    params = urllib.urlencode ({
        'privatekey': private_key,
        'remoteip' : remoteip,
        'challenge': recaptcha_challenge_field,
        'response' : recaptcha_response_field,
        })

    httpresp = urlfetch.fetch(
                   url      = "http://%s/verify" % VERIFY_SERVER,
                   payload  = params,
                   method   = urlfetch.POST,
                   headers  = headers
                    )

    if httpresp.status_code == 200:
        # response was fine

        # get the return values
        return_values = httpresp.content.splitlines();

        # get the return code (true/false)
        return_code = return_values[0]

        if return_code == "true":
            # yep, filled perfectly
            return RecaptchaResponse (is_valid=True)
        else:
            # nope, something went wrong
            return RecaptchaResponse (is_valid=False, error_code = return_values [1])
    else:
        # recaptcha server was not reachable
        return RecaptchaResponse (is_valid=False, error_code = "recaptcha-not-reachable")

if GAE:
    submit = submit_gae

from pyxer.template.genshi import HTML

# Default keys for *.appspot.com
_pub_key = "6LcrngQAAAAAAC1iVJGsWhkkpu4Fx3Z_pDCKkbvF"
_private_key = "6LcrngQAAAAAAFtRJVKFZ6d-BJxZK-40BAdURQ30"

def html(pub_key=_pub_key, use_ssl=False):
    if pub_key == _pub_key:
        log.warn("PLEASE GET YOUR OWN RECAPTCHA KEYS ON http://www.recaptcha.net!")
    return HTML(displayhtml(
        pub_key,
        use_ssl = use_ssl,
        error = req.params.get("error")))

def test(private_key=_private_key):
    if private_key == _private_key:
        log.warn("PLEASE GET YOUR OWN RECAPTCHA KEYS ON http://www.recaptcha.net!")
    remoteip = req.environ['REMOTE_ADDR']
    cResponse = submit(
        req.params.get('recaptcha_challenge_field'),
        req.params.get('recaptcha_response_field'),
        private_key,
        remoteip)
    req.captcha_error = cResponse.error_code
    return cResponse.is_valid
