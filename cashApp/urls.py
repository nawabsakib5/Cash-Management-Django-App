from django.urls import path
from cashApp.views import *

urlpatterns = [
    path('', transaction_list, name='transaction_list'),
    path('add/', transaction_create, name='transaction_create'),
    path('<int:pk>/edit/', transaction_edit, name='transaction_edit'),
    path('<int:pk>/delete/',transaction_delete, name='transaction_delete'),
]
