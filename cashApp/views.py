import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import io
from django.db import transaction as db_transaction
from .models import CustomUser, Transaction, Project, AuditLog, AdminProfile, Category, SubCategory, ProjectPermission, DynamicRow
from .forms import *
from .decorators import admin_required, not_frozen, log_action
from .utils import *


from google.oauth2 import service_account
from googleapiclient.discovery import build

# আপনার গুগল শিটের আইডিটি এখানে বসান
SPREADSHEET_ID = "YOUR_GOOGLE_SPREADSHEET_ID_HERE" 


def sync_to_google_sheet(transaction):
    
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            'google_credentials.json', scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        entry_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        
        category_name = transaction.sub_category.category.name if transaction.sub_category else "Uncategorized"
        sub_category_name = transaction.sub_category.name if transaction.sub_category else "Uncategorized"

        row_data = [
            transaction.project.name,                           
            transaction.title,                                  
            transaction.type.upper(),                           
            category_name,              
            sub_category_name,                                 
            float(transaction.amount),                          
            transaction.user.username,                         
            transaction.date.strftime('%Y-%m-%d'),              
            entry_time                                          
        ]

        body = {'values': [row_data]}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{transaction.project.name}'!A:I",  
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Google Sheet Sync Error: {e}")
        return False


def create_google_sheet_tab(project):
    
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            'google_credentials.json', scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=creds)
        
        
        body = {
            'requests': [
                {
                    'addSheet': {
                        'properties': {
                            'title': project.name
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        
        if project.is_dynamic:
            headers = project.dynamic_fields
        else:
            headers = ['Project Name', 'Purpose / Title', 'Flow Type', 'Main Category', 'Sub Category', 'Amount', 'Contributor', 'Transaction Date', 'Entry Timestamp']
        
        header_body = {'values': [headers]}
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{project.name}'!A1",  
            valueInputOption="RAW",
            body=header_body
        ).execute()
        
        return True
    except Exception as e:
        print(f"Google Sheet Create Tab Error: {e}")
        return False


def sync_dynamic_row_to_sheet(dynamic_row):
    
    try:
        project = dynamic_row.project
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            'google_credentials.json', scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        
        row_data = []
        for header in project.dynamic_fields:
            row_data.append(dynamic_row.data.get(header, ''))

        body = {'values': [row_data]}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{project.name}'!A:Z",  
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Dynamic Sheet Sync Error: {e}")
        return False


@admin_required
def admin_export_project_data(request, pk):
    
    project = get_object_or_404(Project, pk=pk)
    transactions = project.transactions.filter(is_deleted=False).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="project_{project.name}_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Project', 'Title', 'Type', 'Category', 'Sub-Category', 'Amount (BDT)', 'Contributor', 'Date'])

    for tx in transactions:
        
        category_name = tx.sub_category.category.name if tx.sub_category else "Uncategorized"
        sub_category_name = tx.sub_category.name if tx.sub_category else "Uncategorized"

        writer.writerow([
            project.name,
            tx.title,
            tx.type.upper(),
            category_name,
            sub_category_name,
            tx.amount,
            tx.user.username,
            tx.date.strftime('%Y-%m-%d')
        ])

    return response


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
            user_type = 'user',
            password  = password,
        )
        login(request, user)
        send_welcome_email(user)
        messages.success(request, f"Welcome {username}! Your account has been created.")
        
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
        send_password_change_email(request.user)
        messages.success(request, "Password changed successfully.")
        return redirect('project_list')

    return render(request, 'change_password.html')


# ─── Project Views ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def project_list(request):
    if request.user.is_admin:
        projects = Project.objects.select_related('user').prefetch_related('members').all().order_by('-created_at')
    else:
        
        hidden_project_ids = ProjectPermission.objects.filter(
            user=request.user, access_level='hide'
        ).values_list('project_id', flat=True)

        owned  = request.user.owned_projects.exclude(id__in=hidden_project_ids)
        joined = request.user.joined_projects.exclude(id__in=hidden_project_ids)
        projects = (owned | joined).distinct().order_by('-created_at')
        
    return render(request, 'project_list.html', {
        'projects': projects,
        'is_admin_view': request.user.is_admin,
    })


@login_required(login_url='login')
@not_frozen
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project      = form.save(commit=False)
            project.user = request.user
            project.save()
            
            create_google_sheet_tab(project)
            
            log_action(request.user, 'create', target=project, request=request)
            messages.success(request, "Project created successfully.")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})



@login_required(login_url='login')
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    is_admin_view = request.user.is_admin
    is_owner      = request.user == project.user
    is_member     = request.user in project.members.all()

    
    user_permission = None
    if not is_admin_view and not is_owner:
        user_perm_obj = project.user_permissions.filter(user=request.user).first()
        if user_perm_obj:
            user_permission = user_perm_obj.access_level
            if user_permission == 'hide':
                messages.error(request, "You do not have permission to access this project.")
                return redirect('project_list')
        elif not is_member:
            messages.error(request, "You do not have permission to access this project.")
            return redirect('project_list')

    
    can_edit = is_admin_view or is_owner or (user_permission == 'edit') or (not user_permission and is_member)

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

    if not is_admin_view:
        transactions = transactions.exclude(delete_requested=True)

    
    dynamic_rows_data = []
    if project.is_dynamic:
        for row in project.dynamic_rows.select_related('user').all():
            row_values = []
            for header in project.dynamic_fields:
                row_values.append(row.data.get(header, ''))
            dynamic_rows_data.append({
                'values': row_values,
                'user': row.user
            })

    return render(request, 'project_detail.html', {
        'project':          project,
        'transactions':     transactions,
        'total_income':     project.total_income(),
        'total_expense':    project.total_expense(),
        'balance':          project.balance(),
        'balance_warning':  project.balance() < 0,
        'contributions':    project.contribution_summary(),
        'is_owner':         is_owner,
        'is_admin_view':    is_admin_view,
        'today':            today,
        'active_type':      tx_type,
        'active_month':     month_filter,
        'active_amount':    amount_range,
        'active_date_from': date_from,
        'active_date_to':   date_to,
        'can_edit':         can_edit,  
        'dynamic_rows_data': dynamic_rows_data, 
    })

@login_required(login_url='login')
@not_frozen
def project_edit(request, pk):
    if request.user.is_admin:
        project = get_object_or_404(Project, pk=pk)
    else:
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
    if request.user.is_admin:
        project = get_object_or_404(Project, pk=pk)
    else:
        project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect('project_list')
    return render(request, 'project_confirm_delete.html', {'project': project})



@login_required(login_url='login')
@not_frozen
def project_members(request, pk):
    if request.user.is_admin:
        project = get_object_or_404(Project, pk=pk)
    else:
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
    if request.user.is_admin:
        project = get_object_or_404(Project, pk=pk)
    else:
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

    is_admin_view = request.user.is_admin
    if not is_admin_view and request.user != project.user and request.user not in project.members.all():
        messages.error(request, "You don't have permission to add transactions to this project.")
        return redirect('project_list')

    balance = project.balance()

    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            tx_type = form.cleaned_data.get('type')
            amount  = form.cleaned_data.get('amount')

            tx         = form.save(commit=False)
            tx.user    = request.user
            tx.project = project
            tx.save()

            sync_to_google_sheet(tx)

            send_transaction_confirmation(tx)

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
        form = TransactionForm(user=request.user)

    return render(request, 'transaction_form.html', {
        'form': form, 'project': project, 'balance': balance,
        'is_admin_view': is_admin_view,
    })



@login_required(login_url='login')
@not_frozen
def transaction_edit(request, pk):
    if request.user.is_admin:
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            log_action(request.user, 'edit', target=transaction, request=request)
            messages.success(request, "Transaction updated successfully.")
            return redirect('project_detail', pk=transaction.project.pk)
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'transaction_form.html', {
        'form': form, 'project': transaction.project,
    })

@login_required(login_url='login')
@not_frozen
def transaction_delete(request, pk):
    if request.user.is_admin:
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    project_pk = transaction.project.pk

    if request.method == 'POST':
        transaction.request_delete()
        admin_emails = list(
            CustomUser.objects.filter(user_type='admin').values_list('email', flat=True)
        )
        send_delete_request_email(transaction, admin_emails)
        log_action(request.user, 'delete_request', target=transaction, request=request)
        return redirect('project_detail', pk=project_pk)

    return render(request, 'transaction_confirm_delete.html', {'transaction': transaction})



@login_required(login_url='login')
@not_frozen
def category_list(request):
    if request.user.is_admin:
        visible_subs = SubCategory.objects.all().prefetch_related('users')
    else:
        visible_subs = SubCategory.objects.filter(
            Q(users__isnull=True) | Q(users=request.user)
        ).distinct().prefetch_related('users')

    categories = Category.objects.prefetch_related(
        Prefetch('subcategories', queryset=visible_subs)
    ).all()

    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.created_by = request.user
            cat.save()
            messages.success(request, f"Category '{cat.name}' created successfully.")
            return redirect('category_list')

    return render(request, 'category_list.html', {
        'categories': categories,
        'form': form,
    })


@login_required(login_url='login')
@not_frozen
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if not request.user.is_admin and category.created_by != request.user:
        messages.error(request, "You don't have permission to delete this category.")
        return redirect('category_list')

    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')

    return render(request, 'category_confirm_delete.html', {'category': category})


@admin_required
def subcategory_create(request):
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            sub = form.save()
            users = sub.users.all()
            if users:
                usernames = ", ".join(u.username for u in users)
                messages.success(request, f"Sub-category '{sub.name}' created — visible only to: {usernames}.")
            else:
                messages.success(request, f"Sub-category '{sub.name}' created — visible to everyone (Global).")
            return redirect('category_list')
    else:
        form = SubCategoryForm()
    return render(request, 'subcategory_form.html', {'form': form})


@admin_required
def subcategory_delete(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        subcategory.delete()
        messages.success(request, "Sub-category deleted successfully.")
        return redirect('category_list')
    return render(request, 'subcategory_confirm_delete.html', {'subcategory': subcategory})


@login_required(login_url='login')
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'subcategories': []})

    subs = SubCategory.objects.filter(
        category_id=category_id
    ).filter(
        Q(users__isnull=True) | Q(users=request.user)
    ).distinct().values('id', 'name')

    return JsonResponse({'subcategories': list(subs)})


# ─── Admin Dashboard Views ─────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    cat_form = CategoryForm()
    sub_form = SubCategoryForm()

    if request.method == 'POST':
        if 'add_category' in request.POST:
            cat_form = CategoryForm(request.POST)
            if cat_form.is_valid():
                cat = cat_form.save(commit=False)
                cat.created_by = request.user
                cat.save()
                messages.success(request, f"Category '{cat.name}' created successfully.")
                return redirect('admin_dashboard')

        elif 'add_subcategory' in request.POST:
            sub_form = SubCategoryForm(request.POST)
            if sub_form.is_valid():
                sub = sub_form.save()
                users = sub.users.all()
                if users:
                    usernames = ", ".join(u.username for u in users)
                    messages.success(request, f"Sub-category '{sub.name}' created — visible only to: {usernames}.")
                else:
                    messages.success(request, f"Sub-category '{sub.name}' created — visible to everyone (Global).")
                return redirect('admin_dashboard')

    categories = Category.objects.prefetch_related(
        Prefetch('subcategories', queryset=SubCategory.objects.all().prefetch_related('users'))
    ).all()

    all_projects = Project.objects.select_related('user').prefetch_related('members').order_by('-created_at')

    projects_with_totals = []
    for p in all_projects:
        projects_with_totals.append({
            'project':  p,
            'income':   p.total_income(),
            'expense':  p.total_expense(),
            'balance':  p.balance(),
            'owner':    p.user,
            'members':  p.members.all(),
        })

    context = {
        'total_income_all':  sum(p.total_income() for p in all_projects),
        'total_expense_all': sum(p.total_expense() for p in all_projects),
        'total_users':        CustomUser.objects.filter(user_type='user').count(),
        'frozen_users':       CustomUser.objects.filter(is_frozen=True).count(),
        'total_projects':     Project.objects.count(),
        'total_transactions': Transaction.objects.filter(is_deleted=False).count(),
        'pending_deletes':    Transaction.objects.filter(
                                  delete_requested=True, is_deleted=False
                              ).count(),
        'recent_logs':        AuditLog.objects.select_related('actor').all()[:20],
        'categories':         categories,
        'cat_form':           cat_form,
        'sub_form':           sub_form,
        'all_projects':       all_projects,
        'projects_with_totals': projects_with_totals,
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
            send_account_unfrozen_email(target_user)
            messages.success(request, f"'{target_user.username}' has been unfrozen.")
        else:
            target_user.is_frozen = True
            target_user.save(update_fields=['is_frozen'])
            log_action(request.user, 'freeze', target=target_user, request=request)
            send_account_frozen_email(target_user)
            messages.success(request, f"'{target_user.username}' has been frozen.")

        return redirect('admin_user_list')

    return render(request, 'admin/user_freeze_confirm.html', {'target_user': target_user})


@admin_required
def admin_user_activity(request, user_id):
    target_user  = get_object_or_404(CustomUser, pk=user_id)
    logs         = AuditLog.objects.filter(actor=target_user).order_by('-timestamp')
    transactions = Transaction.objects.filter(
                       user=target_user, is_deleted=False
                   ).select_related('project').order_by('-date')
    projects     = Project.objects.filter(user=target_user).order_by('-created_at')

    context = {
        'target_user':   target_user,
        'logs':          logs,
        'transactions':  transactions,
        'projects':      projects,
        'total_income':  sum(t.amount for t in transactions if t.type == 'income'),
        'total_expense': sum(t.amount for t in transactions if t.type == 'expense'),
    }
    return render(request, 'admin/user_activity.html', context)


@admin_required
def admin_delete_requests(request):
    pending = Transaction.objects.filter(
        delete_requested=True, is_deleted=False
    ).select_related('user', 'project').order_by('delete_requested_at')
    return render(request, 'admin/delete_requests.html', {'pending': pending})


@admin_required
def admin_delete_confirm(request, pk):
    transaction = get_object_or_404(
        Transaction, pk=pk, delete_requested=True, is_deleted=False)

    if request.method == 'POST':
        transaction.admin_confirm_delete()
        log_action(request.user, 'delete_confirm', target=transaction,
                   detail=f"Confirmed delete of '{transaction.title}'", request=request)
        messages.success(request, f"'{transaction.title}' has been permanently deleted.")
        return redirect('admin_delete_requests')

    return render(request, 'admin/delete_confirm.html', {'transaction': transaction})


@admin_required
def admin_delete_reject(request, pk):
    transaction = get_object_or_404(
        Transaction, pk=pk, delete_requested=True, is_deleted=False)

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


@admin_required
def admin_user_subcategory(request, user_id):
    from .forms import UserSubCategoryForm
    target_user = get_object_or_404(CustomUser, pk=user_id, user_type='user')

    assigned_subs  = SubCategory.objects.filter(users=target_user).select_related('category')
    all_categories = Category.objects.prefetch_related('subcategories').all()

    if request.method == 'POST':

        # ── Unassign action ──
        if 'unassign_sub' in request.POST:
            sub_id = request.POST.get('unassign_sub')
            try:
                sub = SubCategory.objects.get(pk=sub_id)
                sub.users.remove(target_user)
                messages.success(request, f"'{sub.name}' removed from {target_user.username}.")
            except SubCategory.DoesNotExist:
                messages.error(request, "Sub-category not found.")
            return redirect('admin_user_subcategory', user_id=user_id)

        form = UserSubCategoryForm(request.POST)
        if form.is_valid():
            # ── Existing subcategory assign ──
            selected_subs = form.cleaned_data.get('subcategories')
            if selected_subs:
                for sub in selected_subs:
                    sub.users.add(target_user)
                count = selected_subs.count()
                messages.success(
                    request,
                    f"{count} sub-categor{'y' if count == 1 else 'ies'} assigned to {target_user.username}."
                )

            new_name = form.cleaned_data.get('new_sub_category', '').strip()
            new_cat  = form.cleaned_data.get('new_sub_category_cat')
            if new_name and new_cat:
                sub, created = SubCategory.objects.get_or_create(
                    category=new_cat,
                    name=new_name,
                )
                sub.users.add(target_user)
                if created:
                    messages.success(request, f"New sub-category '{new_name}' created and assigned to {target_user.username}.")
                else:
                    messages.success(request, f"Existing sub-category '{new_name}' assigned to {target_user.username}.")

            return redirect('admin_user_subcategory', user_id=user_id)
    else:
        form = UserSubCategoryForm()

    return render(request, 'admin/user_subcategory.html', {
        'target_user':    target_user,
        'form':           form,
        'assigned_subs':  assigned_subs,
        'all_categories': all_categories,
    })



@admin_required
def admin_import_project_sheet(request):
    
    if request.method == 'POST':
        project_name = request.POST.get('project_name', '').strip()
        description = request.POST.get('description', '').strip()
        csv_file = request.FILES.get('csv_file')

        if not project_name or not csv_file:
            messages.error(request, "Project Name and CSV File are required.")
            return render(request, 'admin/import_project.html')

        try:
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string, delimiter=',')
            headers = next(reader)
            headers = [h.strip() for h in headers if h.strip()]

            with db_transaction.atomic():
                
                project = Project.objects.create(
                    name=project_name,
                    description=description,
                    user=request.user,
                    is_dynamic=True,
                    dynamic_fields=headers
                )

                for row in reader:
                    if not row:
                        continue
                    row_dict = {}
                    for i, h in enumerate(headers):
                        if i < len(row):
                            row_dict[h] = row[i].strip()
                    
                    DynamicRow.objects.create(
                        project=project,
                        data=row_dict,
                        user=request.user
                    )

            create_google_sheet_tab(project)

            messages.success(request, f"Dynamic Project '{project_name}' created with {len(headers)} fields!")
            return redirect('project_detail', pk=project.pk)
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return render(request, 'admin/import_project.html')

    return render(request, 'admin/import_project.html')


@admin_required
def admin_manage_project_permissions(request, pk):
    
    project = get_object_or_404(Project, pk=pk)
    users = CustomUser.objects.filter(user_type='user')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        access_level = request.POST.get('access_level')
        target_user = get_object_or_404(CustomUser, pk=user_id)

        perm, created = ProjectPermission.objects.update_or_create(
            project=project,
            user=target_user,
            defaults={'access_level': access_level}
        )
        
        if access_level in ['view', 'edit']:
            project.members.add(target_user)
        else:
            project.members.remove(target_user)

        messages.success(request, f"Permissions updated for {target_user.username} successfully.")
        return redirect('admin_manage_project_permissions', pk=project.pk)

    permissions_map = {p.user_id: p.access_level for p in project.user_permissions.all()}
    for u in users:
        u.current_access_level = permissions_map.get(u.id, 'view')  

    return render(request, 'admin/project_permissions.html', {
        'project': project,
        'users': users,
    })

@login_required(login_url='login')
@not_frozen
def dynamic_entry_create(request, pk):
    
    project = get_object_or_404(Project, pk=pk, is_dynamic=True)
    
    
    if not request.user.is_admin and request.user != project.user:
        user_perm = project.user_permissions.filter(user=request.user).first()
        if not user_perm or user_perm.access_level != 'edit':
            messages.error(request, "You do not have permission to add rows to this project.")
            return redirect('project_detail', pk=project.pk)

    if request.method == 'POST':
        entry_data = {}
        for header in project.dynamic_fields:
            entry_data[header] = request.POST.get(header, '').strip()

        row = DynamicRow.objects.create(
            project=project,
            data=entry_data,
            user=request.user
        )

        sync_dynamic_row_to_sheet(row)

        messages.success(request, "Data entry successfully synchronized!")
        return redirect('project_detail', pk=project.pk)

    return render(request, 'dynamic_entry_form.html', {'project': project})