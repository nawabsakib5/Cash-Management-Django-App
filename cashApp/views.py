# cashApp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, Transaction, Project, AuditLog, AdminProfile
from .forms import (
    TransactionForm, RegisterForm, LoginForm,
    ProjectForm, AdminUserCreateForm, AdminUserEditForm,
)
from .decorators import admin_required, not_frozen, log_action


# ─── Auth Views ────────────────────────────────────────────────────────────────

def Signup(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'admin':
            return redirect('admin_dashboard')
        return redirect('project_list')

    if request.method == 'POST':
        username         = request.POST.get('username')
        full_name        = request.POST.get('full_name')
        phone            = request.POST.get('phone')
        email            = request.POST.get('email')
        user_type        = request.POST.get('user_type')
        password         = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "This username already exists.")
            return render(request, 'register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "This email already exists.")
            return render(request, 'register.html')

        user = CustomUser.objects.create_user(
            username  = username,
            full_name = full_name or '',
            phone     = phone or '',
            email     = email,
            user_type = user_type or 'user',
            password  = password,
        )
        login(request, user)
        messages.success(request, f"Welcome {username}! Your account has been created.")
        if user.user_type == 'admin':
            return redirect('admin_dashboard')
        return redirect('project_list')

    return render(request, 'register.html')


def Login(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'admin':
            return redirect('admin_dashboard')
        return redirect('project_list')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter your username and password.")
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            log_action(user, 'login', detail='Logged in', request=request)
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            return redirect('project_list')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'login.html')

    return render(request, 'login.html')


def logoutpage(request):
    if request.user.is_authenticated:
        log_action(request.user, 'logout', detail='Logged out', request=request)
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def changapassword(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_pass')
        new_pass = request.POST.get('new_pass')
        con_pass = request.POST.get('con_pass')

        if not request.user.check_password(old_pass):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'change_password.html')

        if new_pass != con_pass:
            messages.error(request, "New passwords do not match.")
            return render(request, 'change_password.html')

        if len(new_pass) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'change_password.html')

        request.user.set_password(new_pass)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password changed successfully.")
        return redirect('project_list')

    return render(request, 'change_password.html')


# ─── Project Views ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def project_list(request):
    owned  = request.user.owned_projects.all()
    joined = request.user.joined_projects.all()
    projects = (owned | joined).distinct().order_by('-created_at')
    return render(request, 'project_list.html', {'projects': projects})


@login_required(login_url='login')
@not_frozen
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project      = form.save(commit=False)
            project.user = request.user
            project.save()
            log_action(request.user, 'create', target=project, request=request)
            messages.success(request, "Project created successfully.")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})


@login_required(login_url='login')
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.user and request.user not in project.members.all():
        messages.error(request, "You do not have permission to access this project.")
        return redirect('project_list')

    today        = timezone.now().date()
    transactions = project.transactions.filter(is_deleted=False)
    tx_type      = request.GET.get('type', '')
    month_filter = request.GET.get('month', '')
    amount_range = request.GET.get('amount_range', '')
    date_from    = request.GET.get('date_from', '')
    date_to      = request.GET.get('date_to', '')

    if tx_type in ('income', 'expense'):
        transactions = transactions.filter(type=tx_type)

    if month_filter == 'this':
        transactions = transactions.filter(
            date__month=today.month, date__year=today.year)
    elif month_filter == 'last':
        last_month = today.month - 1 or 12
        last_year  = today.year if today.month > 1 else today.year - 1
        transactions = transactions.filter(
            date__month=last_month, date__year=last_year)

    if amount_range == '0-1000':
        transactions = transactions.filter(amount__lte=1000)
    elif amount_range == '1000+':
        transactions = transactions.filter(amount__gt=1000)

    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    if request.user.user_type != 'admin':
        transactions = transactions.exclude(delete_requested=True)

    return render(request, 'project_detail.html', {
        'project':          project,
        'transactions':     transactions,
        'total_income':     project.total_income(),
        'total_expense':    project.total_expense(),
        'balance':          project.balance(),
        'balance_warning':  project.balance() < 0,
        'contributions':    project.contribution_summary(),
        'is_owner':         request.user == project.user,
        'today':            today,
        'active_type':      tx_type,
        'active_month':     month_filter,
        'active_amount':    amount_range,
        'active_date_from': date_from,
        'active_date_to':   date_to,
    })


@login_required(login_url='login')
@not_frozen
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            log_action(request.user, 'edit', target=project, request=request)
            messages.success(request, "Project updated successfully.")
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_form.html', {'form': form, 'project': project})


@login_required(login_url='login')
@not_frozen
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect('project_list')
    return render(request, 'project_confirm_delete.html', {'project': project})


# ─── Project Member Views ──────────────────────────────────────────────────────

@login_required(login_url='login')
@not_frozen
def project_members(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        try:
            user_to_add = CustomUser.objects.get(username=username)
            if user_to_add == project.user:
                messages.error(request, "You are the owner and cannot add yourself as a member.")
            elif user_to_add in project.members.all():
                messages.error(request, f"{username} is already a member.")
            else:
                project.members.add(user_to_add)
                messages.success(request, f"{username} has been added to the project.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with that username.")
        return redirect('project_members', pk=pk)

    return render(request, 'project_members.html', {'project': project})


@login_required(login_url='login')
@not_frozen
def project_member_remove(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    member  = get_object_or_404(CustomUser, pk=user_id)
    project.members.remove(member)
    messages.success(request, f"{member.username} has been removed from the project.")
    return redirect('project_members', pk=pk)


# ─── Transaction Views ─────────────────────────────────────────────────────────

@login_required(login_url='login')
@not_frozen
def transaction_create(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.user and request.user not in project.members.all():
        messages.error(request, "You don't have permission to add transactions to this project.")
        return redirect('project_list')

    balance = project.balance()

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx_type = form.cleaned_data.get('type')
            amount  = form.cleaned_data.get('amount')

            tx         = form.save(commit=False)
            tx.user    = request.user
            tx.project = project
            tx.save()
            log_action(request.user, 'create', target=tx,
                       detail=f"{tx_type} {amount}", request=request)

            if tx_type == 'expense' and (balance - amount) < 0:
                messages.warning(
                    request,
                    f"Transaction added, but balance is now negative ({balance - amount})."
                )
            else:
                messages.success(request, "Transaction added successfully.")

            return redirect('project_detail', pk=pk)
    else:
        form = TransactionForm()

    return render(request, 'transaction_form.html', {
        'form': form, 'project': project, 'balance': balance,
    })


@login_required(login_url='login')
@not_frozen
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            log_action(request.user, 'edit', target=transaction, request=request)
            messages.success(request, "Transaction updated successfully.")
            return redirect('project_detail', pk=transaction.project.pk)
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'transaction_form.html', {
        'form': form, 'project': transaction.project,
    })


@login_required(login_url='login')
@not_frozen
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    project_pk  = transaction.project.pk

    if request.method == 'POST':
        transaction.request_delete()
        log_action(request.user, 'delete_request', target=transaction, request=request)
        return redirect('project_detail', pk=project_pk)

    return render(request, 'transaction_confirm_delete.html', {'transaction': transaction})


# ─── Admin Dashboard Views ─────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    context = {
        'total_users':        CustomUser.objects.filter(user_type='user').count(),
        'frozen_users':       CustomUser.objects.filter(is_frozen=True).count(),
        'total_projects':     Project.objects.count(),
        'total_transactions': Transaction.objects.filter(is_deleted=False).count(),
        'pending_deletes':    Transaction.objects.filter(
                                  delete_requested=True, is_deleted=False
                              ).count(),
        'recent_logs':        AuditLog.objects.select_related('actor').all()[:20],
    }
    return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(username__icontains=query) | \
                users.filter(email__icontains=query)
    return render(request, 'admin/user_list.html', {'users': users, 'query': query})


@admin_required
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            if user.user_type == 'admin':
                AdminProfile.objects.get_or_create(user=user)

            log_action(request.user, 'user_create', target=user,
                       detail=f"User '{user.username}' created by admin", request=request)
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('admin_user_list')
    else:
        form = AdminUserCreateForm()
    return render(request, 'admin/user_form.html', {'form': form, 'action': 'Create'})


@admin_required
def admin_user_edit(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            if target_user.user_type == 'admin':
                AdminProfile.objects.get_or_create(user=target_user)
            log_action(request.user, 'edit', target=target_user,
                       detail=f"User '{target_user.username}' edited by admin", request=request)
            messages.success(request, f"User '{target_user.username}' updated successfully.")
            return redirect('admin_user_list')
    else:
        form = AdminUserEditForm(instance=target_user)
    return render(request, 'admin/user_form.html', {
        'form': form, 'action': 'Edit', 'target_user': target_user,
    })


@admin_required
def admin_user_delete(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)

    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_user_list')

    if request.method == 'POST':
        username = target_user.username
        log_action(request.user, 'user_delete',
                   detail=f"User '{username}' deleted by admin", request=request)
        target_user.delete()
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('admin_user_list')

    return render(request, 'admin/user_confirm_delete.html', {'target_user': target_user})


@admin_required
def admin_user_freeze(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)

    if target_user == request.user:
        messages.error(request, "You cannot freeze your own account.")
        return redirect('admin_user_list')

    if request.method == 'POST':
        if target_user.is_frozen:
            target_user.is_frozen = False
            target_user.save(update_fields=['is_frozen'])
            log_action(request.user, 'unfreeze', target=target_user, request=request)
            messages.success(request, f"'{target_user.username}' has been unfrozen.")
        else:
            target_user.is_frozen = True
            target_user.save(update_fields=['is_frozen'])
            log_action(request.user, 'freeze', target=target_user, request=request)
            messages.success(request, f"'{target_user.username}' has been frozen.")

        return redirect('admin_user_list')

    return render(request, 'admin/user_freeze_confirm.html', {'target_user': target_user})


@admin_required
def admin_delete_requests(request):
    pending = Transaction.objects.filter(
        delete_requested=True, is_deleted=False
    ).select_related('user', 'project').order_by('delete_requested_at')

    return render(request, 'admin/delete_requests.html', {'pending': pending})


@admin_required
def admin_delete_confirm(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, delete_requested=True, is_deleted=False)

    if request.method == 'POST':
        transaction.admin_confirm_delete()
        log_action(request.user, 'delete_confirm', target=transaction,
                   detail=f"Confirmed delete of '{transaction.title}'", request=request)
        messages.success(request, f"'{transaction.title}' has been permanently deleted.")
        return redirect('admin_delete_requests')

    return render(request, 'admin/delete_confirm.html', {'transaction': transaction})


@admin_required
def admin_delete_reject(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, delete_requested=True, is_deleted=False)

    if request.method == 'POST':
        transaction.delete_requested    = False
        transaction.delete_requested_at = None
        transaction.save(update_fields=['delete_requested', 'delete_requested_at'])
        log_action(request.user, 'edit', target=transaction,
                   detail=f"Delete request rejected for '{transaction.title}'", request=request)
        messages.success(request, f"Delete request for '{transaction.title}' has been rejected.")
        return redirect('admin_delete_requests')

    return render(request, 'admin/delete_confirm.html', {
        'transaction': transaction, 'reject_mode': True,
    })


@admin_required
def admin_audit_log(request):
    logs = AuditLog.objects.select_related('actor').all()

    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)

    user_filter = request.GET.get('user', '').strip()
    if user_filter:
        logs = logs.filter(actor__username__icontains=user_filter)

    date_filter = request.GET.get('date', '').strip()
    if date_filter:
        logs = logs.filter(timestamp__date=date_filter)

    context = {
        'logs':           logs[:200],
        'action_choices': AuditLog.ACTION_CHOICES,
        'action_filter':  action_filter,
        'user_filter':    user_filter,
        'date_filter':    date_filter,
    }
    return render(request, 'admin/audit_log.html', context)