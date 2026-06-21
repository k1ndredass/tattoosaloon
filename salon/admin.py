from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Tattoo, TattooStyle, Appointment, Review, CartItem, Lead, CareProduct


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone', 'avatar')}),
    )


@admin.register(TattooStyle)
class TattooStyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Tattoo)
class TattooAdmin(admin.ModelAdmin):
    list_display = ['title', 'master', 'style', 'price', 'is_active', 'created_at']
    list_filter = ['style', 'is_active', 'master', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'master', 'date', 'time', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'date', 'master']
    search_fields = ['client__username', 'master__username']
    readonly_fields = ['created_at', 'items_summary', 'total_price']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'master', 'tattoo', 'rating', 'is_moderated', 'created_at']
    list_filter = ['rating', 'is_moderated', 'created_at']
    search_fields = ['author__username', 'text']
    readonly_fields = ['created_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'tattoo', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'tattoo__title']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'lead_type', 'preferred_master', 'processed', 'created_at']
    list_filter = ['lead_type', 'processed', 'created_at']
    search_fields = ['name', 'phone', 'email', 'comment']
    readonly_fields = ['created_at']


@admin.register(CareProduct)
class CareProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['title', 'description']


