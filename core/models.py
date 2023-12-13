import os
import uuid
from django.conf import settings

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import( 
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from random import randint
import datetime
from cpf_field import models as modelCPF

def user_image_field(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    return os.path.join('uploads', 'user', filename)


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
    
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_supersuser = True
        user.save(using=self._db)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=False)
    last_name = models.CharField(max_length=255, null=False)
    cpf = modelCPF.CPFField('cpf')
    url_image = models.ImageField(null=True, upload_to=user_image_field)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    login_attempts = models.PositiveIntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
class Account(models.Model):
    agency = models.CharField(max_length=4)
    number = models.CharField(max_length=16)
    nickname = models.CharField(max_length=255)
    user = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.agency} {self.number}"
    
class Transfer(models.Model):
    sender = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="sender", null=True)
    receiver = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="receiver", null=True)
    value = models.DecimalField(max_digits=10,decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

class Loan(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    installments = models.IntegerField()
    request_date = models.DateTimeField(default=timezone.now)
    payed = models.BooleanField(default=False)
    value = models.DecimalField(max_digits=10, decimal_places=2) # original value
    fees = models.DecimalField(max_digits=5,decimal_places=3, default=1.025) # % of fees

class LoanInstallments(models.Model):
    loanId = models.ForeignKey(Loan, on_delete=models.CASCADE)
    payed_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=False)
    value = models.DecimalField(max_digits=10,decimal_places=2) # value with fee added

class Credit(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    installments = models.IntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    payed = models.BooleanField(default=False)

class CreditInstallments(models.Model):
    creditId = models.ForeignKey(Credit, on_delete=models.PROTECT)
    payed_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=False)
    value = models.DecimalField(max_digits=10,decimal_places=2)
