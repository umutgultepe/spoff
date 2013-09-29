from yahoo.application import OAuthApplication
from django.conf import settings


def get_yahoo_profile(access_token):
    auth_token = AccessToken.from_string(access_token)
    oauthapp = OAuthApplication(
        settings.YAHOO_CONSUMER_KEY,
        settings.YAHOO_CONSUMER_SECRET,
        settings.YAHOO_APPLICATION_ID,
        settings.YAHOO_CALLBACK_URL
    )
    oauthapp.token = auth_token
    profile = oauthapp.getProfile()
    return profile