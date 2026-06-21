from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Общие страницы
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('catalog/', views.catalog, name='catalog'),
    path('tattoo/<int:pk>/', views.tattoo_detail, name='tattoo_detail'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('contacts/', views.contacts, name='contacts'),
    
    # Корзина
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:tattoo_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('care/', views.care_products, name='care_products'),
    path('care/add/<str:product_id>/', views.add_care_addon, name='add_care_addon'),
    path('care/remove/<str:product_id>/', views.remove_care_addon, name='remove_care_addon'),
    path('care/attach-active/', views.cart_attach_to_active_appointment, name='cart_attach_active'),
    
    # Записи на сеансы
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('api/available-times/', views.get_available_times, name='get_available_times'),
    path('lead/submit/', views.submit_lead, name='submit_lead'),
    path('api/available-times/', views.get_available_times, name='get_available_times'),
    
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Кабинет администратора (кастомный, чтобы не конфликтовал с Django admin)
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/users/create/', views.admin_user_create, name='admin_user_create'),
    path('dashboard/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('dashboard/users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('dashboard/reviews/', views.admin_reviews, name='admin_reviews'),
    path('dashboard/reviews/<int:pk>/<str:action>/', views.admin_review_moderate, name='admin_review_moderate'),
    path('dashboard/tattoos/', views.admin_tattoos, name='admin_tattoos'),
    path('dashboard/tattoos/create/', views.admin_tattoo_create, name='admin_tattoo_create'),
    path('dashboard/tattoos/<int:pk>/edit/', views.admin_tattoo_edit, name='admin_tattoo_edit'),
    path('dashboard/tattoos/<int:pk>/delete/', views.admin_tattoo_delete, name='admin_tattoo_delete'),
    path('dashboard/appointments/', views.admin_appointments, name='admin_appointments'),
    path('dashboard/appointments/<int:pk>/edit/', views.admin_appointment_edit, name='admin_appointment_edit'),
    path('dashboard/appointments/<int:pk>/delete/', views.admin_appointment_delete, name='admin_appointment_delete'),
    path('dashboard/care-products/', views.admin_care_products, name='admin_care_products'),
    path('dashboard/care-products/create/', views.admin_care_product_create, name='admin_care_product_create'),
    path('dashboard/care-products/<int:pk>/edit/', views.admin_care_product_edit, name='admin_care_product_edit'),
    path('dashboard/care-products/<int:pk>/delete/', views.admin_care_product_delete, name='admin_care_product_delete'),
    
    # Тату-мастер
    path('master/tattoos/', views.master_tattoos, name='master_tattoos'),
    path('master/tattoos/create/', views.master_tattoo_create, name='master_tattoo_create'),
    path('master/tattoos/<int:pk>/edit/', views.master_tattoo_edit, name='master_tattoo_edit'),
    path('master/tattoos/<int:pk>/delete/', views.master_tattoo_delete, name='master_tattoo_delete'),
]

