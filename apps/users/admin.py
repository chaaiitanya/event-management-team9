from django.contrib import admin
from apps.users.models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'created_at', 'updated_at']
    search_fields = ['email', 'name']
    list_filter = ['is_admin', 'is_active', 'is_staff', 'is_superuser',]
    list_per_page = 10