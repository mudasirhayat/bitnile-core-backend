from django.db import models

# Create your models here.



class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimestampMixin):
    first_name=models.CharField(max_length=50,default="")
    last_name=models.CharField(max_length=50,default="")
    email = models.EmailField(max_length=254,null=True,default="",blank=True)
    phone = models.CharField(max_length=20, default="",null=True,blank=True)
    is_uploaded=models.BooleanField(default=False,null=True,blank=True)
    url=models.CharField(max_length=200,null=True, blank=True)
    facebook_share = models.IntegerField(default=0)
    twitter_share = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    visits=models.IntegerField(default=0)

    def __str__(self):
        return str(self.first_name+" "+self.last_name)