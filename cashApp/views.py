# cashApp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, Transaction, Project
from .forms import TransactionForm, RegisterForm, LoginForm, ProjectForm


# ─── Auth Views ────────────────────────────────────────────────────────────────

def Signup(request):
    if request.user.is_authenticated:
        return redirect('project_list')

    if request.method == 'POST':
        username         = request.POST.get('username')
        full_name        = request.POST.get('full_name')
        phone            = request.POST.get('phone')
        email            = request.POST.get('email')
        user_type        = request.POST.get('user_type')
        password         = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not all([username, email, password, confirm_password]):
            messages.error(request, "সব field পূরণ করো।")
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, "Password দুটো মিলছে না।")
            return render(request, 'register.html')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "এই username আগে থেকেই আছে।")
            return render(request, 'register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "এই email আগে থেকেই আছে।")
            return render(request, 'register.html')

        # Create user
        user = CustomUser.objects.create_user(
            username  = username,
            full_name = full_name or '',
            phone     = phone or '',
            email     = email,
            user_type = user_type or 'user',
            password  = password,
        )
        login(request, user)
        messages.success(request, f"স্বাগতম {username}! Account তৈরি হয়েছে।")
        return redirect('project_list')

    return render(request, 'register.html')


def Login(request):
    if request.user.is_authenticated:
        return redirect('project_list')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Username ও Password দাও।")
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('project_list')
        else:
            messages.error(request, "Username বা Password ভুল।")
            return render(request, 'login.html')

    return render(request, 'login.html')


def logoutpage(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def changapassword(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_pass')
        new_pass = request.POST.get('new_pass')
        con_pass = request.POST.get('con_pass')

        if not request.user.check_password(old_pass):
            messages.error(request, "Previous Password Not Match")
            return render(request, 'change_password.html')

        if new_pass != con_pass:
            messages.error(request, "Password Not Matched")
            return render(request, 'change_password.html')

        if len(new_pass) < 8:
            messages.error(request, "Password Must Be 8 Digit")
            return render(request, 'change_password.html')

        request.user.set_password(new_pass)
        request.user.save()
        update_session_auth_hash(request, request.user)  
        messages.success(request, "Password Successfully Changed")
        return redirect('project_list')

    return render(request, 'change_password.html')


# ─── Project Views ─────────────────────────────────────────────────────────────

@login_required(login_url='login')
def project_list(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'project_list.html', {'projects': projects})


@login_required(login_url='login')
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project      = form.save(commit=False)
            project.user = request.user
            project.save()
            messages.success(request, "Project তৈরি হয়েছে।")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})


@login_required(login_url='login')
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    today   = timezone.now().date()

    transactions = project.transactions.all()
    tx_type      = request.GET.get('type', '')
    month_filter = request.GET.get('month', '')
    amount_range = request.GET.get('amount_range', '')

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

    return render(request, 'project_detail.html', {
        'project':         project,
        'transactions':    transactions,
        'total_income':    project.total_income(),
        'total_expense':   project.total_expense(),
        'balance':         project.balance(),
        'balance_warning': project.balance() < 0,
        'today':           today,
        'active_type':     tx_type,
        'active_month':    month_filter,
        'active_amount':   amount_range,
    })


@login_required(login_url='login')
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project update হয়েছে।")
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_form.html', {'form': form, 'project': project})


@login_required(login_url='login')
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project delete হয়েছে।")
        return redirect('project_list')
    return render(request, 'project_confirm_delete.html', {'project': project})


# ─── Transaction Views ─────────────────────────────────────────────────────────

@login_required(login_url='login')
def transaction_create(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    balance = project.balance()

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx_type = form.cleaned_data.get('type')
            amount  = form.cleaned_data.get('amount')

            if tx_type == 'expense' and (balance - amount) < 0:
                form.add_error(None, f"এই expense করলে balance negative হবে (৳{balance - amount})।")
                return render(request, 'transaction_form.html', {
                    'form': form, 'project': project,
                    'balance': balance, 'balance_warning': True,
                })

            tx         = form.save(commit=False)
            tx.user    = request.user
            tx.project = project
            tx.save()
            messages.success(request, "Transaction যোগ হয়েছে।")
            return redirect('project_detail', pk=pk)
    else:
        form = TransactionForm()

    return render(request, 'transaction_form.html', {
        'form': form, 'project': project, 'balance': balance,
    })


@login_required(login_url='login')
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction update হয়েছে।")
            return redirect('project_detail', pk=transaction.project.pk)
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'transaction_form.html', {
        'form': form, 'project': transaction.project,
    })


@login_required(login_url='login')
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    project_pk  = transaction.project.pk
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction delete হয়েছে।")
        return redirect('project_detail', pk=project_pk)
    return render(request, 'transaction_confirm_delete.html', {'transaction': transaction})