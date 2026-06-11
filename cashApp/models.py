# cashApp/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True)
    phone     = models.CharField(max_length=20, blank=True)
    email     = models.EmailField(unique=True)

    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('user',  'User'),
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='user'
    )

    def __str__(self):
        return self.username


class Project(models.Model):
    user        = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects')
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_income(self):
        return sum(t.amount for t in self.transactions.filter(type='income'))

    def total_expense(self):
        return sum(t.amount for t in self.transactions.filter(type='expense'))

    def balance(self):
        return self.total_income() - self.total_expense()

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('income',  'Income'),
        ('expense', 'Expense'),
    )
    user    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    title  = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type   = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    date   = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.type})"

    class Meta:
        ordering = ['-date']