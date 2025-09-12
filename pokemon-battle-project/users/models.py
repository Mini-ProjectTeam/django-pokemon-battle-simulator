from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    profile_image = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default.png',
        verbose_name='프로필 이미지'
    )
    status_message = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='상태 메시지'
    )
    wins = models.IntegerField(default=0, verbose_name='승리')
    losses = models.IntegerField(default=0, verbose_name='패배')


