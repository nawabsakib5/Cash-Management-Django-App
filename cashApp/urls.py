# cashApp/urls.py

from django.urls import path
from cashApp.views import *

urlpatterns = [
    path('register/',        Signup,         name='signup'),
    path('login/',           Login,          name='login'),
    path('logout/',          logoutpage,     name='logout'),
    path('change-password/', changapassword, name='changapassword'),

    path('',                          project_list,   name='project_list'),
    path('projects/create/',          project_create, name='project_create'),
    path('projects/<int:pk>/',        project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/',   project_edit,   name='project_edit'),
    path('projects/<int:pk>/delete/', project_delete, name='project_delete'),

    path('projects/<int:pk>/members/',                  project_members,       name='project_members'),
    path('projects/<int:pk>/members/<int:user_id>/remove/', project_member_remove, name='project_member_remove'),

    path('projects/<int:pk>/add/',        transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/',   transaction_edit,   name='transaction_edit'),
    path('transactions/<int:pk>/delete/', transaction_delete, name='transaction_delete'),
]