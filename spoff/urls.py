from django.conf.urls import patterns, include, url
from spoff.api import UserResource, TableResource
from tastypie.api import Api
from spoff.views import HomePage

api = Api(api_name='v1')
api.register(UserResource())
api.register(TableResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'spoff_app.views.home', name='home'),
    # url(r'^spoff_app/', include('spoff_app.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', HomePage.as_view()),
    url(r'^api/', include(api.urls)),
)
