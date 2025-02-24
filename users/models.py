from django.db import models
from django.contrib.auth.models import AbstractUser#, AbstractBaseUser, BaseUserManager

# class CustomUserManager(BaseUserManager):
  
#   def create_user(self, username, password=None, **extra_fields):
#     if not username:
#         raise ValueError('The Username field must be set')
    
#     user = self.model(username=username, **extra_fields)

#     if password:
#         user.set_password(password)  # Hash the password

#     user.save(using=self._db)
#     return user
  
#   def create_superuser(self, username, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(username, password, **extra_fields)

class User(AbstractUser):#(AbstractBaseUser)
  # name = models.CharField(max_length=200)
  # email = models.EmailField(unique=True)
  # bio = models.TextField(null=True)
  # username = models.CharField(max_length=255, uniquwe=True)
  avatar = models.ImageField(null=True, default="avatar.svg")

  # objects = CustomUserManager()

  # USERNAME_FIELD = 'username'


  # USERNAME_FIELD = 'email'
  # REQUIRED_FIELDS = []

  def __str__(self):
    return self.username
