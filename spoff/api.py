from spoff.models import User


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        


class TableResource(ModelResource):
    class Meta:
        queryset = Table.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        
            
    
    
    
        
        
    