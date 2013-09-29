from django.conf import settings
from yahoo.application import OAuthApplication
from yahoo.oauth import AccessToken


def get_yahoo_profile(access_token, secret_token):
    oauthapp = OAuthApplication(
        settings.YAHOO_CONSUMER_KEY,
        settings.YAHOO_CONSUMER_SECRET,
        settings.YAHOO_APPLICATION_ID,
        settings.YAHOO_CALLBACK_URL
    )
    auth_token  = AccessToken(access_token, secret_token)
    oauthapp.token = auth_token
    profile = oauthapp.getProfile()
    return profile