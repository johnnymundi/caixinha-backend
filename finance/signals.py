from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Category

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_categories(sender, instance, created, **kwargs):
    if not created:
        return
    Category.objects.get_or_create(user=instance, name="Outros")
