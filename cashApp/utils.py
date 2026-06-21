# cashApp/utils.py

from django.core.mail import send_mail
from django.conf import settings


def send_welcome_email(user):
    subject = "Welcome to CashManager!"
    message = f"""Hi {user.username},

Welcome to CashManager! Your account has been created successfully.

You can now:
- Create projects to track your cash flow
- Add income and expense transactions
- Collaborate with team members

Login here: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'your app URL'}

Best regards,
CashManager Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def send_transaction_confirmation(transaction):
    subject = f"Transaction Added — {transaction.title}"
    message = f"""Hi {transaction.user.username},

A new transaction has been recorded:

Title   : {transaction.title}
Amount  : ৳{transaction.amount}
Type    : {transaction.type.capitalize()}
Project : {transaction.project.name if transaction.project else '—'}
Date    : {transaction.date}

If you did not make this transaction, please contact the admin immediately.

Best regards,
CashManager Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [transaction.user.email],
        fail_silently=True,
    )


def send_delete_request_email(transaction, admin_emails):
    subject = f"Delete Request — {transaction.title}"
    message = f"""A user has requested to delete a transaction.

Details:
User    : {transaction.user.username} ({transaction.user.email})
Title   : {transaction.title}
Amount  : ৳{transaction.amount}
Type    : {transaction.type.capitalize()}
Project : {transaction.project.name if transaction.project else '—'}
Date    : {transaction.date}

Please review and approve or reject this request from the admin panel.

Best regards,
CashManager System
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=True,
    )


def send_password_change_email(user):
    subject = "Your Password Has Been Changed"
    message = f"""Hi {user.username},

Your CashManager password was recently changed.

If you made this change, no action is needed.

If you did NOT make this change, please contact the admin immediately.

Best regards,
CashManager Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def send_account_frozen_email(user):
    """Admin account freeze করলে user-কে notify করবে"""
    subject = "Your Account Has Been Frozen"
    message = f"""Hi {user.username},

Your CashManager account has been temporarily frozen by an administrator.

You will not be able to log in or make changes until your account is unfrozen.

If you believe this is a mistake, please contact the admin.

Best regards,
CashManager Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def send_account_unfrozen_email(user):
    subject = "Your Account Has Been Restored"
    message = f"""Hi {user.username},

Your CashManager account has been restored and is now active again.

You can log in and continue using the platform.

Best regards,
CashManager Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )