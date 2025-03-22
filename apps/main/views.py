from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from apps.main.models import Event,Registration
from apps.main.forms import EventForm, RegistrationForm
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count, Avg, Q
from apps.users.models import Account
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    # Get current date for filtering
    now = timezone.now()
    
    # Basic statistics
    stats = {
        'total_events': Event.objects.count(),
        'total_users': Account.objects.count(),
        'total_registrations': Registration.objects.filter(status='confirmed').count(),
    }
    
    avg_rating = 4.8  # Placeholder
    
    stats['avg_rating'] = avg_rating
    
    # Get upcoming events (limited to 3 for the dashboard)
    upcoming_events = Event.objects.filter(
        start_date__gt=now,
        status='published'
    ).order_by('start_date')[:3]
    
    # Event statistics by status
    event_stats = {
        'upcoming': Event.objects.filter(start_date__gt=now, status='published').count(),
        'ongoing': Event.objects.filter(start_date__lte=now, end_date__gte=now, status='published').count(),
        'completed': Event.objects.filter(end_date__lt=now, status='published').count(),
        'draft': Event.objects.filter(status='draft').count(),
        'cancelled': Event.objects.filter(status='cancelled').count(),
    }
    
    # Registration statistics by month (for charts)
    monthly_registrations = Registration.objects.filter(
        updated_at__year=now.year
    ).annotate(
        month=TruncMonth('updated_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Recent registrations
    recent_registrations = Registration.objects.select_related('user', 'event').order_by('-updated_at')[:5]
    
    # Popular events (most registrations)
    popular_events = Event.objects.annotate(
        registration_count=Count('registrations', filter=Q(registrations__status='confirmed'))
    ).order_by('-registration_count')[:5]
    
    context = {
        'stats': stats,
        'upcoming_events': upcoming_events,
        'event_stats': event_stats,
        'monthly_registrations': monthly_registrations,
        'recent_registrations': recent_registrations,
        'popular_events': popular_events,
        'page': 'dashboard',
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def events(request):
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    events = Event.objects.all()
    
    # Apply search filter
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        events = events.filter(category=category_filter)
    
    # Apply status filter
    if status_filter:
        now = timezone.now()
        if status_filter == 'upcoming':
            events = events.filter(start_date__gt=now)
        elif status_filter == 'ongoing':
            events = events.filter(start_date__lte=now, end_date__gte=now)
        elif status_filter == 'completed':
            events = events.filter(end_date__lt=now)
        elif status_filter == 'canceled':
            events = events.filter(status='cancelled')
    
    # Annotate with registration counts
    events = events.annotate(registration_count=Count('registrations', filter=Q(registrations__status__in=['pending', 'confirmed'])))
    
    # Order by start date (upcoming first)
    events = events.order_by('start_date')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(events, 10)  # Show 10 events per page
    events_page = paginator.get_page(page)
    
    # Get categories for filter dropdown
    categories = Event.CATEGORY_CHOICES
    
    # Get statistics for quick stats cards
    now = timezone.now()
    stats = {
        'active_events': Event.objects.filter(status='published', end_date__gte=now).count(),
        'total_registrations': Registration.objects.filter(status='confirmed').count(),
        'upcoming_events': Event.objects.filter(status='published', start_date__gt=now).count(),
        'completed_events': Event.objects.filter(end_date__lt=now).count(),
    }
    
    context = {
        'events': events_page,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'stats': stats,
        'page': 'events',
    }
    
    return render(request, 'events.html', context)


def users(request):
    return render(request, 'users.html', {
        'page': 'users',
    })
    
def tickets(request):
    return render(request, 'tickets.html', {
        'page': 'tickets',
    })
    
def feedback(request):
    return render(request, 'feedback.html', {
        'page': 'feedback',
    })
    
def analytics(request):
    return render(request, 'analytics.html', {
        'page': 'analytics',
    })
    
def settings(request):
    return render(request, 'settings.html', {
        'page': 'settings',
    })

@login_required
def create_event(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create events. Please contact an administrator or log in as a staff user.")
        return redirect('users:login')
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            
            messages.success(request, f"Event '{event.title}' created successfully!")
            return redirect(reverse('main:event_detail', args=[event.slug]))
    else:
        form = EventForm()
    
    return render(request, 'create_event.html', {
        'form': form,
        'page': 'create_event',
        'title': 'Create New Event'
    })

def event_detail(request, slug):
    # Get the event or return 404 if not found
    event = get_object_or_404(Event, slug=slug)
    
    # If event is in draft status, only allow the creator or staff to view it
    if event.status == 'draft' and not (request.user == event.created_by or request.user.is_staff):
        return HttpResponseForbidden("You don't have permission to view this event.")
    
    is_registered = False
    
    # Get related events (same category, excluding current one)
    related_events = Event.objects.filter(
        category=event.category, 
        status='published'
    ).exclude(id=event.id).order_by('-start_date')[:3]
    
    context = {
        'event': event,
        'page': 'event_detail',
        'is_registered': is_registered,
        'related_events': related_events,
        'can_edit': request.user.is_authenticated and (request.user == event.created_by or request.user.is_staff),
    }
    
    return render(request, 'event_detail.html', context)

@login_required
def edit_event(request, slug):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit events. Please contact an administrator or log in as a staff user.")
        return redirect('users:login')
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user has permission to edit this event
    if not (request.user == event.created_by or request.user.is_staff):
        messages.error(request, "You don't have permission to edit this event.")
        return HttpResponseForbidden("You don't have permission to edit this event.")
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated_event = form.save()
            
            messages.success(request, f"Event '{updated_event.title}' updated successfully!")
            return redirect(reverse('main:event_detail', args=[updated_event.slug]))
    else:
        form = EventForm(instance=event)
    
    return render(request, 'edit_event.html', {
        'form': form,
        'event': event,
        'page': 'edit_event',
        'title': f'Edit Event: {event.title}'
    })

@login_required
def delete_event(request, slug):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete events. Please contact an administrator or log in as a staff user.")
        return redirect('users:login')
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user has permission to delete this event
    if not (request.user == event.created_by or request.user.is_staff):
        messages.error(request, "You don't have permission to delete this event.")
        return HttpResponseForbidden("You don't have permission to delete this event.")
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f"Event '{event_title}' has been deleted.")
        return redirect('main:events')
    
    # If not POST, redirect to edit page
    return redirect('main:edit_event', slug=slug)

@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')
    
    # Check if event is open for registration
    if not event.registration_open:
        messages.error(request, "Registration for this event is closed.")
        return redirect('main:event_detail', slug=event.slug)
    
    # Check if event is full
    if event.capacity > 0:
        current_registrations = Registration.objects.filter(
            event=event, 
            status__in=['pending', 'confirmed']
        ).count()
        
        if current_registrations >= event.capacity:
            messages.error(request, "This event has reached its capacity.")
            return redirect('main:event_detail', slug=event.slug)
    
    # Check if user is already registered
    existing_registration = Registration.objects.filter(event=event, user=request.user).first()
    if existing_registration:
        if existing_registration.status == 'cancelled':
            # If previously cancelled, reactivate
            existing_registration.status = 'pending'
            existing_registration.save()
            messages.success(request, f"Your registration for '{event.title}' has been reactivated.")
            return redirect('main:event_detail', slug=event.slug)
        else:
            messages.info(request, "You are already registered for this event.")
            return redirect('main:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user
            registration.status = 'confirmed'  # Auto-confirm for simplicity
            registration.save()
            
            messages.success(request, f"You have successfully registered for '{event.title}'.")
            return redirect('main:event_detail', slug=event.slug)
    else:
        form = RegistrationForm()
    
    return render(request, 'register_event.html', {
        'form': form,
        'event': event,
        'page': 'register_event',
    })

@login_required
def cancel_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(Registration, event=event, user=request.user)
    
    # Check if registration can be cancelled
    if not registration.can_cancel:
        messages.error(request, "This registration cannot be cancelled.")
        return redirect('main:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        registration.status = 'cancelled'
        registration.save()
        
        messages.success(request, f"Your registration for '{event.title}' has been cancelled.")
        return redirect('main:event_detail', slug=event.slug)
    
    return render(request, 'cancel_registration.html', {
        'registration': registration,
        'event': event,
        'page': 'cancel_registration',
    })

@login_required
def my_registrations(request):
    # Get all active registrations for the user
    active_registrations = Registration.objects.filter(
        user=request.user,
        status='confirmed',
        event__end_date__gte=timezone.now()
    ).select_related('event').order_by('event__start_date')
    
    # Get past registrations
    past_registrations = Registration.objects.filter(
        user=request.user,
        event__end_date__lt=timezone.now()
    ).select_related('event').order_by('-event__start_date')
    
    # Get cancelled registrations
    cancelled_registrations = Registration.objects.filter(
        user=request.user,
        status='cancelled'
    ).select_related('event').order_by('-registration_date')
    
    return render(request, 'my_registrations.html', {
        'active_registrations': active_registrations,
        'past_registrations': past_registrations,
        'cancelled_registrations': cancelled_registrations,
        'page': 'my_registrations',
    })
