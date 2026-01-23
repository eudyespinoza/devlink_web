from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    
    # Usuarios
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Productos
    path('products/', views.products_list, name='products_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Productos de usuario
    path('users/<int:user_id>/products/', views.user_products, name='user_products'),
    path('users/<int:user_id>/products/add/', views.add_user_product, name='add_user_product'),
    path('users/<int:user_id>/product-status/', views.update_user_product_status, name='update_user_product_status'),
    path('users/<int:user_id>/remove-product/', views.remove_user_product, name='remove_user_product'),
    
    # Reportes WhatsApp
    path('whatsapp-report/<int:user_id>/', views.whatsapp_report, name='whatsapp_report'),
    
    # Consultas de Contacto
    path('contact-requests/', views.contact_requests_list, name='contact_requests'),
    path('contact-requests/<int:contact_id>/', views.contact_request_detail, name='contact_request_detail'),
    path('contact-requests/<int:contact_id>/delete/', views.contact_request_delete, name='contact_request_delete'),
]