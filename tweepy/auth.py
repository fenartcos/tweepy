#Embedded file name: /home/aaron/repos/tweepy/tweepy/auth.py
import six
from tweepy.error import TweepError
from tweepy.api import API
import requests
from requests_oauthlib import OAuth1Session, OAuth1
from six.moves.urllib.parse import parse_qs

class AuthHandler(object):

    def apply_auth(self, url, method, headers, parameters):
        """Apply authentication headers to request"""
        raise NotImplementedError

    def get_username(self):
        """Return the username of the authenticated user"""
        raise NotImplementedError


class OAuthHandler(AuthHandler):
    """OAuth authentication handler"""
    OAUTH_HOST = 'api.twitter.com'
    OAUTH_ROOT = '/oauth/'

    def __init__(self, consumer_key, consumer_secret, callback=None, secure=True):
        if type(consumer_key) == six.text_type:
            consumer_key = six.binary_type(consumer_key, 'utf-8')

        if type(consumer_secret) == six.text_type:
            consumer_secret = six.binary_type(consumer_secret, 'utf-8')

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = None
        self.access_token_secret = None
        self.callback = callback
        self.username = None
        self.secure = secure
        self.oauth = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri=self.callback)

    def _get_oauth_url(self, endpoint, secure=True):
        if self.secure or secure:
            prefix = 'https://'
        else:
            prefix = 'http://'
        return prefix + self.OAUTH_HOST + self.OAUTH_ROOT + endpoint

    def apply_auth(self):
        return OAuth1(self.consumer_key, client_secret=self.consumer_secret, resource_owner_key=self.access_token, resource_owner_secret=self.access_token_secret)

    def _get_request_token(self):
        try:
            url = self._get_oauth_url('request_token')
            return self.oauth.fetch_request_token(url)
        except Exception as e:
            raise TweepError(e)

    def set_access_token(self, key, secret):
        self.access_token = key
        self.access_token_secret = secret

    def get_authorization_url(self, signin_with_twitter = False):
        """Get the authorization URL to redirect the user"""
        try:
            if signin_with_twitter:
                url = self._get_oauth_url('authenticate')
            else:
                url = self._get_oauth_url('authorize')
            self.request_token = self._get_request_token()
            return self.oauth.authorization_url(url)
        except Exception as e:
            raise TweepError(e)

    def get_access_token(self, verifier = None):
        """
        After user has authorized the request token, get access token
        with user supplied verifier.
        """
        try:
            url = self._get_oauth_url('access_token')
            self.oauth = OAuth1Session(self.consumer_key, client_secret=self.consumer_secret, resource_owner_key=self.request_token['oauth_token'], resource_owner_secret=self.request_token['oauth_token_secret'], verifier=verifier, callback_uri=self.callback)
            resp = self.oauth.fetch_access_token(url)
            self.access_token = resp['oauth_token']
            self.access_token_secret = resp['oauth_token_secret']
            return (self.access_token, self.access_token_secret)
        except Exception as e:
            raise TweepError(e)

    def get_xauth_access_token(self, username, password):
        """
        Get an access token from an username and password combination.
        In order to get this working you need to create an app at
        http://twitter.com/apps, after that send a mail to api@twitter.com
        and request activation of xAuth for it.
        """
        try:
            url = self._get_oauth_url('access_token', secure=True)
            oauth = OAuth1(self.consumer_key, client_secret=self.consumer_secret)
            r = requests.post(url=url, auth=oauth, headers={'x_auth_mode':
                'client_auth', 'x_auth_username': username, 'x_auth_password':
                password})

            credentials = parse_qs(r.content)
            return (credentials.get('oauth_token')[0], credentials.get('oauth_token_secret')[0])
        except Exception as e:
            raise TweepError(e)

    def get_username(self):
        if self.username is None:
            api = API(self)
            user = api.verify_credentials()
            if user:
                self.username = user.screen_name
            else:
                raise TweepError('Unable to get username, invalid oauth token!')
        return self.username
