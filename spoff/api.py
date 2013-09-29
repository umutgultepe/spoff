from django.conf.urls.defaults import url
from django.contrib.auth.models import AnonymousUser
from django.http.response import HttpResponseBadRequest, HttpResponse
from push_notifications.models import GCMDevice
from spoff.models import User, Table, TableManager
from spoff.utils import get_yahoo_profile
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import ReadOnlyAuthorization, Authorization
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest, HttpNotFound, HttpConflict
from tastypie.models import ApiKey
from tastypie.resources import ModelResource
from tastypie.utils.urls import trailing_slash
from django.shortcuts import get_object_or_404
import json

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

    def user_data_response(self, request, user=None):
        if user is None:
            user = request.user
        return self.create_response(request, {
            "id": user.id,
            "email": user.email,
            "yahoo_id": user.yahoo_id,
            "username": user.username,
            "key": ApiKey.objects.get_or_create(user=user)[0].key,
            "karma": user.karma
        })
        
    def get_list(self, request, **kwargs):
        return self.user_data_response(request)

        
    def unlocked(self, request, **kwargs):
        self.is_authenticated(request)
        request.user.add_karma(-50)
        t_list = request.user.joined_tables.all()
        if t_list.exists():
            data = json.dumps({"id": request.user.id, "username": request.user.username})
            for table in t_list:
                m_list = table.members.exclude(pk=request.user.pk)
                for m in m_list:
                    devs = GCMDevice.objects.filter(user=m)
                    for dev in devs:
                        try:
                            dev.send_message(data)
                        except GCMError, e:
                            print e
                            continue                
        else:
            HttpNotFound(json.dumps({"error": "User is not part of a table"}))
        return self.user_data_response(request)
                
    def post_list(self, request, **kwargs):
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        keys = ["access_token", "secret_token", "device_id", "registration_id"]
        for k in keys:
            if k not in data:
                raise ImmediateHttpResponse(HttpResponseBadRequest("missing data"))
            
        profile = get_yahoo_profile(data["access_token"], data["secret_token"])
        device_id = data.pop("device_id")
        registration_id = data.pop("registration_id")
            
        try:
            u = User.objects.get(yahoo_id=profile["guid"])
        except User.DoesNotExist:
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
        return self.user_data_response(request, u)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/unlocked%s$" % (self._meta.resource_name, trailing_slash(),),
                self.wrap_view('unlocked'), name="api_unlocked_phone"),
        ]            


class TableResource(ModelResource):
    class Meta:
        queryset = Table.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        allowed_methods = ['get', 'post', 'delete']
        fields = ["creator", "date_created", "code", "id"]
        always_return_data = True
        detail_uri_name = 'code'
                
    def obj_create(self, bundle, **kwargs):
        creator = bundle.request.user
        code = bundle.data.get("code", Table.objects.get_unique_code())
        if not Table.objects.check_unique_code(code):
            raise ImmediateHttpResponse(HttpConflict(json.dumps({"error": "Table code already exists"})))
        bundle = super(TableResource, self).obj_create(bundle, code=code, creator=creator, **kwargs)
        bundle.obj.members.add(bundle.request.user)
        return bundle
            
    def dehydrate(self, bundle):
        m_list = []
        for u in bundle.obj.members.all():
            m_list.append({"id": u.id, "username": u.username})
        bundle.data["members"] = m_list
        bundle.data["creator_id"] = bundle.obj.creator_id
        return bundle
    
    def join_table(self, request, code, **kwargs):
        self.is_authenticated(request)
        table = get_object_or_404(Table, code=code)
        if not request.user.join_table(table.id):
            raise ImmediateHttpResponse(HttpBadRequest())
        kwargs["code"] = code
        return self.get_detail(request, **kwargs)

    def leave_table(self, request, code, **kwargs):
        self.is_authenticated(request)
        table = get_object_or_404(Table, code=code)
        if not request.user.leave_table(table.id):
            raise ImmediateHttpResponse(HttpBadRequest())
        kwargs["code"] = code
        return self.get_detail(request, **kwargs)
   
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<code>\S+)/join%s$" % (self._meta.resource_name, trailing_slash(),),
                self.wrap_view('join_table'), name="api_join_table"),
            url(r"^(?P<resource_name>%s)/(?P<code>\S+)/leave%s$" % (self._meta.resource_name, trailing_slash(),),
                self.wrap_view('leave_table'), name="api_join_table"),
        ]
        