from django.contrib import admin
from apps.main.models import Event, Registration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'start_date', 'end_date', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'start_date', 'end_date', 'location']
    search_fields = ['title', 'location', 'description']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'full_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['event__title', 'full_name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def full_name(self, obj):
        return obj.get_full_name()
    
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'full_name'
    