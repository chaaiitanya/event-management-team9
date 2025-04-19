from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('events/', views.events, name='events'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),
    path('events/<slug:slug>/edit/', views.edit_event, name='edit_event'),
    path('events/<slug:slug>/delete/', views.delete_event, name='delete_event'),
    path('events/<int:event_id>/register/', views.register_event, name='register_event'),
    path('events/<int:event_id>/cancel-registration/', views.cancel_registration, name='cancel_registration'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('users/', views.users, name='users'),
    path('tickets/', views.tickets, name='tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/view/', views.view_ticket, name='view_ticket'),
    path('tickets/<int:ticket_id>/edit/', views.edit_ticket, name='edit_ticket'),
    path('tickets/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),
    path('account-information/', views.all_settings, name='settings'),
    path('comments/', views.comments_management, name='comments_management'),
    path('comments/reply/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    path('comments/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comments/export/', views.export_comments, name='export_comments'),

]