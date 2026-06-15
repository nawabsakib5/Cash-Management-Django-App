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


class Category(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'


class SubCategory(models.Model):
    category   = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='subcategories'
    )
    name       = models.CharField(max_length=100)

    
    users      = models.ManyToManyField(
        CustomUser, blank=True, related_name='private_subcategories',
        help_text="Leave empty for a global sub-category visible to everyone. "
                  "Select one or more users to make this sub-category visible only to them."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.users.exists():
            usernames = ", ".join(u.username for u in self.users.all())
            return f"{self.category.name} → {self.name} (Private: {usernames})"
        return f"{self.category.name} → {self.name}"

    class Meta:
        ordering = ['name']
        unique_together = ['category', 'name']
        verbose_name_plural = 'Sub Categories'

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
        null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transactions'
    )
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transactions'
    )
    title      = models.CharField(max_length=150)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    type       = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    date       = models.DateField(default=timezone.now)

    
    is_deleted           = models.BooleanField(default=False)
    delete_requested     = models.BooleanField(default=False)
    delete_requested_at  = models.DateTimeField(null=True, blank=True)
    deleted_at           = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.type})"

    def request_delete(self):
        self.delete_requested    = True
        self.delete_requested_at = timezone.now()
        self.save(update_fields=['delete_requested', 'delete_requested_at'])

    def admin_confirm_delete(self):
        self.is_deleted       = True
        self.deleted_at       = timezone.now()
        self.delete_requested = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'delete_requested'])

    class Meta:
        ordering = ['-date']


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create',         'Created'),
        ('edit',           'Edited'),
        ('delete_request', 'Requested Delete'),
        ('delete_confirm', 'Confirmed Delete'),
        ('login',          'Logged In'),
        ('logout',         'Logged Out'),
        ('freeze',         'Frozen'),
        ('unfreeze',       'Unfrozen'),
        ('user_create',    'User Created'),
        ('user_delete',    'User Deleted'),
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