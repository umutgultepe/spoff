"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import TestCase
from push_notifications.models import GCMDevice
from spoff.models import User, Table
from tastypie.models import ApiKey
from tastypie.test import ResourceTestCase
from uuid import uuid4
import json
from mock import patch

actual_mobile_notifications = []

def _fake_gcm_send_message(**kwargs):

    global actual_mobile_notifications
    actual_mobile_notifications.append(kwargs)
        

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
        new_user.join_table(1)
        self.assertEqual(table.members.count(), 2, "member not joined")


class ApiTestCase(ResourceTestCase):
    #fixtures = ['site_data.json']

    def assertHttpOk(self, response):
        self.assertEqual(response.status_code, 200)

    def assertHttpNotFound(self, response):
        self.assertEqual(response.status_code, 404)

    def get_credentials(self, user):
        key = ApiKey.objects.get_or_create(user=user)[0]
        return self.create_apikey(user.yahoo_id, key.key)

    def prepare_data(self):
        self.user = User.objects.create(username="umut@yahoo.com", email='umut@yahoo.com', yahoo_id="21394u02193")
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
            #===================================================================
            # "device_id": uuid4(),
            # "registration_id": "3fh38",
            #===================================================================
            "first_name": "Umut",
            "last_name": "Gultepe"
        }
        
        self.table_code = "dinners_stuff"
        self.table_data = {"code": self.table_code}
    
    def post_user_data(self):
        resp = self.api_client.post("/api/v1/user/", data=self.user_data, **self.json_headers)
        self.assertHttpOK(resp)
        user = json.loads(resp.content)
        self.assertIn("id", user)
        self.assertIn("email", user)
        self.assertIn("key", user)
        self.assertIn("karma", user)
    
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
        self.assertEqual(self.user.karma, user["karma"])
        self.assertEqual(ApiKey.objects.get(user=self.user).key, user["key"]) 
        
    def test_cannot_get_details_without_authentication(self):
        resp = self.api_client.get("/api/v1/user/", **self.json_headers)
        self.assertHttpUnauthorized(resp)

    @patch('push_notifications.gcm.gcm_send_message', side_effect=_fake_gcm_send_message)
    def test_unlock_notification(self, _fake_gcm_send_message):
        dev = GCMDevice.objects.create(user=self.user, device_id=uuid4(), registration_id="1243")
        dev.save()
        
        resp = self.api_client.post("/api/v1/table/", data=self.table_data, **self.headers)
        self.assertHttpCreated(resp)
        table = Table.objects.get(pk=json.loads(resp.content)["id"])
        
        new_user = User.objects.create(**self.user_data)
        new_headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.get_credentials(new_user)
        }
        
        resp = self.api_client.post("/api/v1/table/%s/join/" % table.code, data=self.table_data, **new_headers)
        self.assertHttpOk(resp)
        
        global actual_mobile_notifications
        actual_mobile_notifications = []
        
        resp = self.api_client.get("/api/v1/user/unlocked/", **new_headers)
        self.assertHttpOk(resp)
        
        self.assertEqual(len(actual_mobile_notifications), 1)
        self.assertEqual(dev.registration_id, actual_mobile_notifications[0]["registration_id"])
        self.assertDictEqual(
            json.loads(actual_mobile_notifications[0]["data"]["msg"]),
            {"id": new_user.id, "username": new_user.username, "table_code": table.code}
        )

    def test_karma_cycle(self):
        resp = self.api_client.post("/api/v1/table/", data=self.table_data, **self.headers)
        self.assertHttpCreated(resp)
        table = Table.objects.get(pk=json.loads(resp.content)["id"])
        
        new_user = User.objects.create(**self.user_data)
        new_headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.get_credentials(new_user)
        }
        
        resp = self.api_client.post("/api/v1/table/%s/join/" % table.code, data=self.table_data, **new_headers)
        self.assertHttpOk(resp)
        new_user = User.objects.get(pk=new_user.pk)
        self.assertEqual(new_user.karma, 100)
        resp = self.api_client.get("/api/v1/user/unlocked/", **new_headers)
        self.assertHttpOk(resp)
        new_user = User.objects.get(pk=new_user.pk)
        self.assertEqual(new_user.karma, 50)
        
        
class TableApiTestCase(ApiTestCase):
    
    def setUp(self):
        super(TableApiTestCase,self).setUp()
        self.user_data = {
            "yahoo_id": "ifdsg",
            "yahoo_token": "abc",
            "email": "lasmdfsamd@yahoo.com",
            "username": "asfdmn"
        }
        self.table_code = "dinners_stuff"
        self.table_data = {"code": self.table_code}
    
    def create_table(self):
        resp = self.api_client.post("/api/v1/table/", data=self.table_data, **self.headers)
        return resp
                
    def test_create_delete_table(self):
        resp = self.create_table()
        self.assertHttpCreated(resp)
        self.assertEqual(Table.objects.count(), 1)
        table = json.loads(resp.content)
        self.assertIn("id", table)
        self.assertIn("members", table)
        self.assertIn("creator_id", table)
        self.assertEqual(Table.objects.latest("pk").members.count(),1)
        self.assertEqual(table["code"], self.table_code)       
        resp = self.api_client.delete("/api/v1/table/%s/" % table["code"], **self.headers)
        self.assertHttpAccepted(resp)
        self.assertEqual(Table.objects.count(), 0)

    def test_cannot_duplicate_table_code(self):
        resp = self.create_table()
        self.assertHttpCreated(resp)
        self.assertEqual(Table.objects.count(), 1)
        resp = self.create_table()
        self.assertHttpConflict(resp)

    def test_get_table_details(self):
        resp = self.create_table()
        self.assertHttpCreated(resp)
        self.assertEqual(Table.objects.count(), 1)
        table = json.loads(resp.content)
        resp = self.api_client.get("/api/v1/table/%s/" % table["code"], **self.headers)
        self.assertHttpOk(resp)
        table = json.loads(resp.content)
        self.assertIn("id", table)
        self.assertIn("members", table)
        self.assertIn("creator_id", table)
        
    def test_join_leave_table(self):
        resp = self.create_table()
        self.assertHttpCreated(resp)
        self.assertEqual(Table.objects.count(), 1)
        
        table = json.loads(resp.content)
        
        new_user = User.objects.create(**self.user_data)
        new_headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.get_credentials(new_user)
        }
        
        only_table = Table.objects.get(pk=table["id"])
        # Join a table1
        resp = self.api_client.post("/api/v1/table/%s/join/" % self.table_code, **new_headers)
        self.assertHttpOk(resp)
        self.assertEqual(only_table.members.count(), 2)
        
        # leave a table
        resp = self.api_client.post("/api/v1/table/%s/leave/" % self.table_code, **new_headers)
        self.assertHttpOk(resp)
        self.assertEqual(only_table.members.count(), 1)
        
    def test_second_join_leaves_first_table(self):
        resp = self.create_table()
        self.assertHttpCreated(resp)
        self.assertEqual(Table.objects.count(), 1)
        
        table = json.loads(resp.content)
        
        new_user = User.objects.create(**self.user_data)
        new_headers = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_AUTHORIZATION': self.get_credentials(new_user)
        }
        
        only_table = Table.objects.get(pk=table["id"])
        # Join a table1
        resp = self.api_client.post("/api/v1/table/%s/join/" % self.table_code, **new_headers)
        self.assertHttpOk(resp)
        self.assertEqual(only_table.members.count(), 2)
        
        new_table = Table.objects.create(code="asdb", creator=self.user)
        new_table.members.add(self.user)
        
        # Join a table1
        resp = self.api_client.post("/api/v1/table/%s/join/" % "asdb", **new_headers)
        self.assertHttpOk(resp)
        old_table = Table.objects.get(pk=table["id"])
        self.assertEqual(old_table.members.count(), 1)       
      
        
class HomePageTestCase(TestCase):
    
    def test_home_page(self):
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)    