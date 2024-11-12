from django.db.models.signals import post_save,pre_save
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Sum
from django.shortcuts import reverse
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    diabled = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    userid = models.CharField(default=False, max_length=30)        
    phone_number = models.CharField(default=False, max_length=30)    
    data_used = models.CharField(default=False, max_length=30)    
    lifetime = models.BooleanField(default=False)
    auto_disable = models.BooleanField(default=False)
    user_name = models.CharField(default=False, max_length=30)
    send = models.CharField(default=False, max_length=30)
    chrome_ext_dis = models.BooleanField(default=False)
    chrome_bot_dis = models.BooleanField(default=False)
    firefox_ext_dis = models.BooleanField(default=False)
    firefox_bot_dis = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username 


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)

post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)