from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import Transaction
from .forms import TransactionForm, RegisterForm, LoginForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('transaction_list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('transaction_list')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('transaction_list')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('transaction_list')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def transaction_list(request):
    today = timezone.now().date()
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    tx_type = request.GET.get('type', '')
    month_filter = request.GET.get('month', '')
    amount_range = request.GET.get('amount_range', '')

    if tx_type in ('income', 'expense'):
        transactions = transactions.filter(type=tx_type)

    if month_filter == 'this':
        transactions = transactions.filter(
            date__month=today.month, date__year=today.year)
    elif month_filter == 'last':
        last_month = today.month - 1 or 12
        last_year = today.year if today.month > 1 else today.year - 1
        transactions = transactions.filter(
            date__month=last_month, date__year=last_year)

    if amount_range == '0-1000':
        transactions = transactions.filter(amount__lte=1000)
    elif amount_range == '1000+':
        transactions = transactions.filter(amount__gt=1000)

    all_tx = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in all_tx if t.type == 'income')
    total_expense = sum(t.amount for t in all_tx if t.type == 'expense')
    balance = total_income - total_expense

    return render(request, 'transaction_list.html', {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'balance_warning': balance < 0,
        'today': today,
        'active_type': tx_type,
        'active_month': month_filter,
        'active_amount': amount_range,
    })


@login_required(login_url='login')
def transaction_create(request):
    all_tx = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in all_tx if t.type == 'income')
    total_expense = sum(t.amount for t in all_tx if t.type == 'expense')
    balance = total_income - total_expense

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx_type = form.cleaned_data.get('type')
            amount = form.cleaned_data.get('amount')
            if tx_type == 'expense' and (balance - amount) < 0:
                form.add_error(None, f"This expense will make your balance negative (৳{balance - amount}).")
                return render(request, 'transaction_form.html', {
                    'form': form,
                    'balance_warning': True,
                    'balance': balance,
                })
            t = form.save(commit=False)
            t.user = request.user
            t.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm()

    return render(request, 'transaction_form.html', {
        'form': form,
        'balance': balance,
    })


@login_required(login_url='login')
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'transaction_form.html', {'form': form})


@login_required(login_url='login')
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transaction_list')
    return render(request, 'transaction_confirm_delete.html', {'transaction': transaction})