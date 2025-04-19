from django.contrib import admin
from apps.main.models import Event, Registration, Comment

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
    
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'short_content', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__username', 'user__email', 'content', 'event__title')
    raw_id_fields = ('user', 'event', 'parent')
    actions = ['approve_comments', 'disapprove_comments']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments have been approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments have been hidden.')
    disapprove_comments.short_description = 'Hide selected comments'
