"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json
from django.test import TestCase
from spoff.models import User
from tastypie.models import ApiKey
from tastypie.test import ResourceTestCase


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
        key = ApiKey.objects.get(user=user)
        return self.create_apikey(user.email, key.key)

    def prepare_data(self):
        self.user = User.objects.create(email='umut@yahoo.com')
        self.credentials = self.get_credentials(self.user)
        self.headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.credentials
        }
    
    def setUp(self):
        self.prepare_data()
        
        
class UserApiTestCase(ApiTestCase):
    
    def test_user_registration(self):
        resp = self.api_client.post("/api/v1/user/", data={"token": "abc", "email": "lasmdfsamd", "device_id": "1239ye89d"})
        self.assertHttpOK(resp)
        user = json.loads(resp)
        self.assertIn("id", user)
        self.assertIn("email", user)
        self.assertIn("key", user)
        
        
    def test_get_my_details(self):
        resp = self.api_client.get("/api/v1/user/", **self.headers)
        self.assertHttpOK(resp)
        user = json.loads(resp)
        self.assertIn("id", user)
        self.assertIn("email", user)
        self.assertIn("key", user)        
        
        

            
    