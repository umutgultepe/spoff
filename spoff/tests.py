"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from tastypie.test import ResourceTestCase
from tastypie.models import ApiKey
from spoff.models import User


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
        