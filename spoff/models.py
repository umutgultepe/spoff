from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
# Create your models here.

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


class User(AbstractUser):
    yahoo_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    yahoo_token = models.CharField(max_length=500, null=True, blank=True)
    karma = models.IntegerField(default=0)
    USERNAME_FIELD = "yahoo_id"
             
    def create_table(self, code=None):
        if code is None:
            code = Table.objects.get_unique_code()
        else:
            if not Table.objects.check_unique_code(code):
                return False
        
        t = Table.objects.create(code=code, creator=self)
        t.save()
        t.members.add(self)
        return t
    
    def join_table(self, pk):
        try:
            table = Table.objects.get(pk=pk)
        except Table.DoesNotExist:
            return False
        self.add_karma(100)
        old_tables = Table.objects.filter(members=self)
        for t in old_tables:
            if t.creator == self:
                t.delete()
            else:
                t.members.remove(self)
        table.members.add(self)
        return True

    def add_karma(self, amount):
        self.karma = self.karma + amount
        self.save()
        
    def leave_table(self, pk):
        try:
            table = Table.objects.get(pk=pk)
        except Table.DoesNotExist:
            return False
        
        table.members.remove(self)
        return True
        
            
class TableManager(models.Manager):
    def check_unique_code(self, code):
        if self.filter(code=code).exists():
            return False
        return True
    
    def get_unique_code(self):
        code = id_generator()
        while not self.check_unique_code(code):
            code = id_generator()
        return code
    
    
class Table(models.Model):
    creator = models.ForeignKey(User, related_name="hosted_tables")
    members = models.ManyToManyField(User, related_name="joined_tables", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=64)
    objects = TableManager()