from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):

    ACADEMIC = "AC"
    COMMERCIAL = "CO"
    UTYPE_CHOICES = (
        (ACADEMIC, 'Academic'),
        (COMMERCIAL, 'Commercial'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    utype = models.CharField(max_length=2,
                             choices=UTYPE_CHOICES,
                             default=ACADEMIC)
    institute = models.CharField(max_length=200)
    position = models.CharField(max_length=30)
    address = models.TextField(null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


