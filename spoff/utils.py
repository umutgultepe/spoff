from django.conf import settings
from yahoo.application import OAuthApplication
from yahoo.oauth import AccessToken


def get_yahoo_profile(request_token, verifier):
    oauthapp = OAuthApplication(
        settings.YAHOO_CONSUMER_KEY,
        settings.YAHOO_CONSUMER_SECRET,
        settings.YAHOO_APPLICATION_ID,
        settings.YAHOO_CALLBACK_URL
    )
    access_token  = oauthapp.get_access_token(request_token, verifier)
    oauthapp.token = access_token
    profile = oauthapp.getProfile()
    return profile