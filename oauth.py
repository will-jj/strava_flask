from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
import json

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class StravaSignIn(OAuthSignIn):
    def __init__(self):
        super(StravaSignIn, self).__init__('strava')
        self.service = OAuth2Service(
            name='strava',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://www.strava.com/oauth/authorize',
            access_token_url='https://www.strava.com/oauth/token',
            base_url='https://www.strava.com/api/v3/',
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='view_private',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None

        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            # params={'format': 'json'},
            decoder=json.loads

        )
        access_token = oauth_session.access_token
        me = oauth_session.get('athlete?').json()

        athlete_id = me.get('id')
        email = me.get('email')
        return (athlete_id, email, access_token)
