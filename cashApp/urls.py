
from django.urls import path
from . import views

urlpatterns = [

    
    path('', views.Login,name='login'),
    path('signup/',views.Signup,name='signup'),
    path('logout/',views.logoutpage,name='logout'),
    path('password/',views.changapassword, name='change_password'),

    path('projects/',views.project_list, name='project_list'),
    path('projects/create/',views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/',views.project_edit,   name='project_edit'),
    path('projects/<int:pk>/delete/',views.project_delete, name='project_delete'),

    path('projects/<int:pk>/members/', views.project_members, name='project_members'),
    path('projects/<int:pk>/members/<int:user_id>/remove/', views.project_member_remove, name='project_member_remove'),

    path('projects/<int:pk>/transactions/add/',views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/',views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/',views.transaction_delete, name='transaction_delete'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/',views.category_delete, name='category_delete'),

    path('categories/subcategory/create/', views.subcategory_create, name='subcategory_create'),
    path('categories/subcategory/<int:pk>/delete/',views.subcategory_delete, name='subcategory_delete'),

    
    path('ajax/subcategories/',views.get_subcategories, name='get_subcategories'),

    
    path('admin-panel/',views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/',views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/create/',views.admin_user_create, name='admin_user_create'),
    path('admin-panel/users/<int:user_id>/edit/',views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:user_id>/delete/',views.admin_user_delete, name='admin_user_delete'),
    path('admin-panel/users/<int:user_id>/freeze/',views.admin_user_freeze, name='admin_user_freeze'),
    path('admin-panel/delete-requests/',views.admin_delete_requests, name='admin_delete_requests'),
    path('admin-panel/delete-requests/<int:pk>/confirm/',views.admin_delete_confirm, name='admin_delete_confirm'),
    path('admin-panel/delete-requests/<int:pk>/reject/',views.admin_delete_reject, name='admin_delete_reject'),
    path('admin-panel/audit-log/',views.admin_audit_log, name='admin_audit_log'),
]