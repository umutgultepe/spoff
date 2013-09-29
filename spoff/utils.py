from django.conf import settings
from yahoo.application import OAuthApplication
from yahoo.oauth import AccessToken
from push_notifications.models import GCMDevice
from spoff.models import User
import json


def test_message(user_id):
    u = User.objects.get(pk=user_id)
    devs = GCMDevice.objects.filter(user=u)
    data = json.dumps({"id": u.id, "username": u.username})
    for dev in devs:
        dev.send_message(data)


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