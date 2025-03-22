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
    path('feedback/', views.feedback, name='feedback'),
    path('analytics/', views.analytics, name='analytics'),
    path('settings/', views.settings, name='settings'),
]