from django.contrib.auth.models import AnonymousUser
from django.http.response import HttpResponseBadRequest
from push_notifications.models import GCMDevice
from spoff.models import User, Table
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import ReadOnlyAuthorization, Authorization
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.models import ApiKey
from tastypie.resources import ModelResource

class UserAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        user = bundle.request.user
        if isinstance(user, AnonymousUser):
            raise Unauthorized("")
        return object_list

    def create_detail(self, object_list, bundle):
        return True

    def read_detail(self, object_list, bundle):
        if bundle.request.user == object_list[0]:
            return True 
        raise Unauthorized("")


class UserAuthentication(ApiKeyAuthentication):
    
    def is_authenticated(self, request, **kwargs):
        if request.method == "POST":
            return True
        return ApiKeyAuthentication.is_authenticated(self, request, **kwargs)

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        authentication = UserAuthentication()
        authorization = Authorization()
        
    def get_list(self, request, **kwargs):
        
        user = request.user
        
        return self.create_response(request, {
            "id": u.id,
            "email": u.email,
            "yahoo_id": u.yahoo_id,
            "username": u.username,
            "key": ApiKey.objects.get_or_create(user=u)[0].key
        })
        
        
    def post_list(self, request, **kwargs):
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        keys = ["yahoo_token", "device_id", "registration_id"]
        for k in keys:
            if k not in data:
                raise ImmediateHttpResponse(HttpResponseBadRequest("missing data"))
            
        profile = get_yahoo_profile(data["yahoo_token"])
            
        try:
            u = User.objects.get(yahoo_id=profile["guid"])
        except User.DoesNotExist:
            device_id = data.pop("device_id")
            registration_id = data.pop("registration_id")
            u = User.objects.create(yahoo_id=profile["guid"], email=profile["guid"] + "@yahoo.com", username=profile["nickname"])
            u.save()
            device, created = GCMDevice.objects.get_or_create(
                device_id=device_id,
                registration_id=registration_id,
                defaults=dict(
                    user=u,
                    active=True
            ))
            if not created:
                if device.user != u:
                    device.user = u
                    device.save()
            else:
                device.save()
        response_data = {
            "id": u.id,
            "email": u.email,
            "yahoo_id": u.yahoo_id,
            "username": u.username,
            "key": ApiKey.objects.get_or_create(user=u)[0].key
        }
        return self.create_response(request, response_data)
            

class TableResource(ModelResource):
    class Meta:
        queryset = Table.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        
            
    
    
    
        
        
    