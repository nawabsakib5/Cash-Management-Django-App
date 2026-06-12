# cashApp/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    full_name  = models.CharField(max_length=150, blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    email      = models.EmailField(unique=True)
    is_frozen  = models.BooleanField(default=False)

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

    @property
    def is_admin(self):
        return self.user_type == 'admin'


class AdminProfile(models.Model):
    user       = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='admin_profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    note       = models.TextField(blank=True)

    def __str__(self):
        return f"Admin: {self.user.username}"


class Project(models.Model):
    user        = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='owned_projects'
    )
    members     = models.ManyToManyField(
        CustomUser, related_name='joined_projects', blank=True
    )
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_income(self):
        return sum(
            t.amount for t in self.transactions.filter(type='income', is_deleted=False)
        )

    def total_expense(self):
        return sum(
            t.amount for t in self.transactions.filter(type='expense', is_deleted=False)
        )

    def balance(self):
        return self.total_income() - self.total_expense()

    def all_members(self):
        ids = set(self.members.values_list('id', flat=True))
        ids.add(self.user_id)
        return CustomUser.objects.filter(id__in=ids)

    def contribution_summary(self):
        summary = []
        for member in self.all_members():
            txs = self.transactions.filter(user=member, is_deleted=False)
            income  = sum(t.amount for t in txs if t.type == 'income')
            expense = sum(t.amount for t in txs if t.type == 'expense')
            summary.append({
                'user':     member,
                'income':   income,
                'expense':  expense,
                'net':      income - expense,
                'is_owner': member.id == self.user_id,
            })
        return summary

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('income',  'Income'),
        ('expense', 'Expense'),
    )
    user    = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='transactions'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    title      = models.CharField(max_length=150)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    type       = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    date       = models.DateField(default=timezone.now)

    # ── Soft Delete ──────────────────────────────────────────────────────────
    is_deleted           = models.BooleanField(default=False)
    delete_requested     = models.BooleanField(default=False)
    delete_requested_at  = models.DateTimeField(null=True, blank=True)
    deleted_at           = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.type})"

    def request_delete(self):
        """User delete করলে শুধু request যাবে, data থাকবে।"""
        self.delete_requested    = True
        self.delete_requested_at = timezone.now()
        self.save(update_fields=['delete_requested', 'delete_requested_at'])

    def admin_confirm_delete(self):
        """Admin confirm করলে তখনই soft-delete হবে।"""
        self.is_deleted       = True
        self.deleted_at       = timezone.now()
        self.delete_requested = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'delete_requested'])

    class Meta:
        ordering = ['-date']


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create',         'তৈরি করেছে'),
        ('edit',           'এডিট করেছে'),
        ('delete_request', 'Delete চেয়েছে'),
        ('delete_confirm', 'Delete Confirm করেছে'),
        ('login',          'Login করেছে'),
        ('logout',         'Logout করেছে'),
        ('freeze',         'Freeze করেছে'),
        ('unfreeze',       'Unfreeze করেছে'),
        ('user_create',    'User তৈরি করেছে'),
        ('user_delete',    'User Delete করেছে'),
    )

    actor       = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action      = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, blank=True)
    target_id   = models.PositiveIntegerField(null=True, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    detail      = models.TextField(blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor} → {self.action} ({self.target_type})"

    class Meta:
        ordering = ['-timestamp']