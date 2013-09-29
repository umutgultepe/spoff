"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import TestCase
from push_notifications.models import GCMDevice
from spoff.models import User
from tastypie.models import ApiKey
from tastypie.test import ResourceTestCase
from uuid import uuid4
import json


class TableTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="umut@yahoo.com", email="umut@yahoo.com")
    
    
    def test_user_can_create_table(self):
        table = self.user.create_table()
        self.assertNotEqual(table.code, "", "empty code")
        self.assertEqual(table.members.count(), 1, "owner not joined")
        
        
    def test_user_can_join_table(self):
        table = self.user.create_table("test_code")
        new_user = User.objects.create(username="julio@yahoo.com", email="julio@yahoo.com")
        new_user.join_table("test_code")
        self.assertEqual(table.members.count(), 2, "member not joined")


class ApiTestCase(ResourceTestCase):
    #fixtures = ['site_data.json']

    def assertHttpOk(self, response):
        self.assertEqual(response.status_code, 200)

    def assertHttpNotFound(self, response):
        self.assertEqual(response.status_code, 404)

    def get_credentials(self, user):
        key = ApiKey.objects.get_or_create(user=user)[0]
        return self.create_apikey(user.email, key.key)

    def prepare_data(self):
        self.user = User.objects.create(username="umut@yahoo.com", email='umut@yahoo.com')
        self.credentials = self.get_credentials(self.user)
        self.json_headers ={
            'CONTENT_TYPE': 'application/json',
        } 
        self.headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.credentials
        }
    
    def setUp(self):
        super(ApiTestCase,self).setUp()
        self.prepare_data()
        
        
class UserApiTestCase(ApiTestCase):
    
    def setUp(self):
        super(UserApiTestCase,self).setUp()
        self.user_data = {
            "yahoo_id": "ifdsg",
            "yahoo_token": "abc",
            "email": "lasmdfsamd@yahoo.com",
            "device_id": uuid4(),
            "registration_id": "3fh38",
            "first_name": "Umut",
            "last_name": "Gultepe"
        }
    
    def post_user_data(self):
        resp = self.api_client.post("/api/v1/user/", data=self.user_data, **self.json_headers)
        self.assertHttpOK(resp)
        user = json.loads(resp.content)
        self.assertIn("id", user)
        self.assertIn("email", user)
        self.assertIn("key", user)
    
    #----------------------------------------- def test_user_registration(self):
        #------------------------------------------------- self.post_user_data()
#------------------------------------------------------------------------------ 
    #--------------------------------------- def test_dont_duplicate_user(self):
        #------------------------------------------------- self.post_user_data()
        #--------- self.assertEqual(User.objects.count(), 2, "Not enouth users")
        #-- self.assertEqual(GCMDevice.objects.count(), 1, "not enough devices")
        #------------------------------------------------- self.post_user_data()
        #----------- self.assertEqual(User.objects.count(), 2, "TOo many users")
        #---- self.assertEqual(GCMDevice.objects.count(), 1, "too many devices")
        
    def test_get_my_details(self):
        resp = self.api_client.get("/api/v1/user/", **self.headers)
        self.assertHttpOK(resp)
        user = json.loads(resp.content)
        self.assertEqual(self.user.id, user["id"])
        self.assertEqual(self.user.email, user["email"])
        self.assertEqual(ApiKey.objects.get(user=self.user).key, user["key"]) 
        
    def test_cannot_get_details_without_authentication(self):
        resp = self.api_client.get("/api/v1/user/", **self.json_headers)
        self.assertHttpUnauthorized(resp)
        
        
class TableApiTestCase(ApiTestCase):
    
    def setUp(self):
        super(TableApiTestCase,self).setUp()
        self.user_data = {
            "yahoo_id": "ifdsg",
            "yahoo_token": "abc",
            "email": "lasmdfsamd@yahoo.com",
            "device_id": uuid4(),
            "registration_id": "3fh38"
        }
    
    def test_create_table(self):
        table_data = {"code": "dinners_stuff"}