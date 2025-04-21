from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from apps.main.models import Event,Registration, Comment, Ticket
from apps.main.forms import EventForm, RegistrationForm, CommentForm, ReplyForm, EditCommentForm
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
import csv
from django.utils import timezone
from django.db.models import Count, Q, Sum
from apps.users.models import Account
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.dateformat import format
from django.db import transaction
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import strip_tags


@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the dashboard. Please contact an administrator or log in as a staff user.")
        return redirect('main:events')
    # Get current date for filtering
    current_date = now()
    
    # Basic statistics
    stats = {
        'total_events': Event.objects.count(),
        'total_users': Account.objects.count(),
        'total_registrations': Registration.objects.filter(status='confirmed').count(),
        'avg_rating': 4.8  # Placeholder
    }
    
    # Get upcoming events (limited to 3 for the dashboard)
    upcoming_events = Event.objects.filter(
        start_date__gt=current_date,
        status='published'
    ).order_by('start_date')[:3]
    
    # Event statistics by status
    event_stats = {
        'upcoming': Event.objects.filter(start_date__gt=current_date, status='published').count(),
        'ongoing': Event.objects.filter(start_date__lte=current_date, end_date__gte=current_date, status='published').count(),
        'completed': Event.objects.filter(end_date__lt=current_date, status='published').count(),
        'draft': Event.objects.filter(status='draft').count(),
        'cancelled': Event.objects.filter(status='cancelled').count(),
    }
    
    # Registration statistics by month (for charts)
    monthly_registrations = Registration.objects.filter(
        updated_at__year=current_date.year
    ).annotate(
        month=TruncMonth('updated_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Format monthly registrations for Chart.js
    formatted_monthly_registrations = [
        {
            'month': format(data['month'], 'M Y'),
            'count': data['count']
        }
        for data in monthly_registrations
    ]
    
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
        'monthly_registrations': formatted_monthly_registrations,
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

@user_passes_test(lambda u: u.is_staff)
def users(request):
    all_users = Account.objects.all()
    return render(request, 'users.html', {
        'page': 'users',
        'users': all_users,
    })
    
def tickets(request):
    return render(request, 'tickets.html', {
        'page': 'tickets',
    })
    
def feedback(request):
    return render(request, 'feedback.html', {
        'page': 'feedback',
    })
       
def all_settings(request):
    return render(request, 'settings.html', {
        'page': 'settings',
    })

@user_passes_test(lambda u: u.is_staff)
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
    event = get_object_or_404(Event, slug=slug)
    comments = event.comments.filter(parent=None, is_approved=True).order_by('-created_at')
    
    # Group tickets by type and get availability counts
    ticket_types = []
    ticket_type_names = set(Ticket.objects.filter(event=event).values_list('type', flat=True).distinct())
    
    for type_name in ticket_type_names:
        tickets = Ticket.objects.filter(event=event, type=type_name)
        available_count = tickets.filter(status='available').count()
        
        if tickets.exists():
            ticket_types.append({
                'name': type_name,
                'price': tickets.first().price,  # Assuming same price for same type
                'available_count': available_count,
            })
    
    # Sort by price
    ticket_types.sort(key=lambda x: x['price'])
    
    # Get query parameters for comment actions
    reply_to = request.GET.get('reply_to')
    edit_comment = request.GET.get('edit_comment')
    
    # Paginate comments
    paginator = Paginator(comments, 10)  # 10 comments per page
    page = request.GET.get('page', 1)
    comments_page = paginator.get_page(page)
    
    # Initialize forms
    comment_form = CommentForm()
    reply_form = ReplyForm()
    edit_form = EditCommentForm()
    
    # Pre-fill edit form if editing a comment
    if edit_comment and request.user.is_authenticated:
        comment_to_edit = get_object_or_404(Comment, id=edit_comment)
        if request.user == comment_to_edit.user or request.user.is_staff:
            print("User is authorized to edit this comment.")
            edit_form = EditCommentForm(instance=comment_to_edit)
        else:
            messages.error(request, "You don't have permission to edit this comment.")
        print(edit_form)
    
    # Handle form submissions
    if request.method == 'POST' and request.user.is_authenticated:
        # Handle comment submission
        if 'comment_submit' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.event = event
                new_comment.user = request.user
                
                # Handle file attachment
                if 'attachment' in request.FILES:
                    attachment = request.FILES['attachment']
                    # Check file size (5MB limit)
                    if attachment.size > 5 * 1024 * 1024:
                        messages.error(request, "File size exceeds 5MB limit.")
                        return redirect(request.path)
                    
                    # Check file extension
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                    ext = attachment.name.split('.')[-1].lower()
                    if not f'.{ext}' in allowed_extensions:
                        messages.error(request, "File type not allowed. Please upload PDF, DOC, DOCX, JPG or PNG.")
                        return redirect(request.path)
                    
                    new_comment.attachment = attachment
                
                new_comment.save()
                
                # If AJAX request, return HTML for the new comment
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    context = {
                        'comment': new_comment,
                        'reply_form': reply_form,
                        'user': request.user,
                    }
                    comment_html = render_to_string('includes/comment.html', context, request)
                    return JsonResponse({
                        'success': True,
                        'comment_html': comment_html,
                        'comment_count': event.comments.filter(is_approved=True).count()
                    })
                
                messages.success(request, "Your comment has been added.")
                return redirect(request.path)
        
        # Handle reply submission
        elif 'reply_submit' in request.POST:
            reply_form = ReplyForm(request.POST)
            parent_id = request.POST.get('parent_id')
            
            if reply_form.is_valid() and parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id, event=event)
                new_reply = reply_form.save(commit=False)
                new_reply.event = event
                new_reply.user = request.user
                new_reply.parent = parent_comment
                
                # Handle file attachment for replies
                if 'attachment' in request.FILES:
                    attachment = request.FILES['attachment']
                    # Check file size (5MB limit)
                    if attachment.size > 5 * 1024 * 1024:
                        messages.error(request, "File size exceeds 5MB limit.")
                        return redirect(request.path)
                    
                    # Check file extension
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                    ext = attachment.name.split('.')[-1].lower()
                    if not f'.{ext}' in allowed_extensions:
                        messages.error(request, "File type not allowed. Please upload PDF, DOC, DOCX, JPG or PNG.")
                        return redirect(request.path)
                    
                    new_reply.attachment = attachment
                
                new_reply.save()
                
                # If AJAX request, return HTML for the new reply
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    context = {
                        'comment': new_reply,
                        'user': request.user,
                    }
                    reply_html = render_to_string('includes/reply.html', context, request)
                    return JsonResponse({
                        'success': True,
                        'reply_html': reply_html,
                        'parent_id': parent_id,
                        'comment_count': event.comments.filter(is_approved=True).count()
                    })
                
                messages.success(request, "Your reply has been added.")
                return redirect(request.path)
        
        # Handle comment editing
        elif 'edit_submit' in request.POST:
            comment_id = request.POST.get('edit_comment_id')
            if comment_id:
                comment_to_edit = get_object_or_404(Comment, id=comment_id)
                if request.user == comment_to_edit.user or request.user.is_staff:
                    edit_form = EditCommentForm(request.POST, request.FILES, instance=comment_to_edit)
                    if edit_form.is_valid():
                        edited_comment = edit_form.save(commit=False)
                        
                        # Handle attachment updates
                        if 'remove_attachment' in request.POST and comment_to_edit.attachment:
                            # Delete the old attachment
                            comment_to_edit.attachment.delete()
                            edited_comment.attachment = None
                        
                        if 'attachment' in request.FILES:
                            attachment = request.FILES['attachment']
                            # Check file size
                            if attachment.size > 5 * 1024 * 1024:
                                messages.error(request, "File size exceeds 5MB limit.")
                                return redirect(request.path)
                            
                            # Check file extension
                            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                            ext = attachment.name.split('.')[-1].lower()
                            if not f'.{ext}' in allowed_extensions:
                                messages.error(request, "File type not allowed.")
                                return redirect(request.path)
                            
                            edited_comment.attachment = attachment
                        
                        edited_comment.save()
                        messages.success(request, "Comment updated successfully.")
                    return redirect(request.path)
        
        # Handle comment deletion
        elif 'delete_comment' in request.POST:
            comment_id = request.POST.get('delete_comment')
            if comment_id:
                comment_to_delete = get_object_or_404(Comment, id=comment_id)
                if request.user == comment_to_delete.user or request.user.is_staff:
                    # Delete attachment if exists
                    if comment_to_delete.attachment:
                        comment_to_delete.attachment.delete()
                    comment_to_delete.delete()
                    messages.success(request, "Comment deleted successfully.")
                return redirect(request.path)
    
    # Check if user is registered for this event
    is_registered = False
    if request.user.is_authenticated:
        is_registered = event.registrations.filter(user=request.user).exists()
    
    # Get related events (same category, excluding current)
    related_events = Event.objects.filter(
        category=event.category,
        status='published'
    ).exclude(id=event.id).order_by('-start_date')[:3]
    
    context = {
        'event': event,
        'comments': comments_page,
        'comment_form': comment_form,
        'reply_form': reply_form,
        'edit_form': edit_form,
        'is_registered': is_registered,
        'related_events': related_events,
        'now': timezone.now(),
        'reply_to': reply_to,
        'edit_comment': edit_comment,
        'ticket_types': ticket_types,
        'can_edit': request.user.is_authenticated and (
            request.user == event.created_by or 
            request.user.is_staff or 
            request.user.has_perm('main.change_event')
        ),
    }
    
    return render(request, 'event_detail.html', context)


def send_registration_confirmation(registration):
    event = registration.event
    user = registration.user

    subject = f"Registration Confirmation for {event.title}"
    
    # Render the HTML content
    html_message = render_to_string('emails/registration_confirmation.html', {
        'user': user,
        'event': event,
        'registration': registration,
        'event_url': settings.SITE_URL + reverse('main:event_detail', kwargs={'slug': event.slug}),
    })
    plain_message = strip_tags(html_message)

    email = EmailMessage(
        subject=subject,
        body=html_message,  # <-- Use HTML content here
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send()


# done by me
@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Check if registration is open
    if not event.registration_open:
        messages.error(request, "Registration for this event is closed.")
        return redirect('main:event_detail', slug=event.slug)
    
    # Check if event is at capacity
    if event.capacity > 0 and event.registrations.count() >= event.capacity:
        messages.error(request, "This event is at full capacity.")
        return redirect('main:event_detail', slug=event.slug)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to register for events.")
        return redirect('account_login')
    
    # Check if user is already registered
    if event.registrations.filter(user=request.user, status='confirmed').exists():
        messages.info(request, "You are already registered for this event.")
        return redirect('main:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        # Get the selected ticket type
        ticket_type = request.POST.get('ticket_type')
        if not ticket_type:
            messages.error(request, "Please select a ticket type.")
            return redirect('main:event_detail', slug=event.slug)
        
        # Find an available ticket of the selected type
        try:
            # Use select_for_update to prevent race conditions
            with transaction.atomic():
                ticket = Ticket.objects.select_for_update().filter(
                    event=event,
                    type=ticket_type,
                    status='available'
                ).first()
                
                if not ticket:
                    messages.error(request, "No tickets of this type are currently available.")
                    return redirect('main:event_detail', slug=event.slug)
                
                # Update ticket status immediately to prevent race conditions
                ticket.status = 'sold'
                ticket.user = request.user
                ticket.save()
                
                # Create registration
                registration = Registration.objects.create(
                    user=request.user,
                    event=event,
                    ticket=ticket,
                    status='confirmed',
                    registration_date=timezone.now()
                )
            
            # Send confirmation email (outside the atomic transaction)
            try:
                send_registration_confirmation(registration)
                messages.success(request, f"You have successfully registered for {event.title}. A confirmation email has been sent.")
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.success(request, f"You have successfully registered for {event.title}, but we couldn't send a confirmation email.")
            
            # Check if this was the last available ticket
            remaining_tickets = Ticket.objects.filter(
                event=event,
                type=ticket_type,
                status='available'
            ).count()
            
            if remaining_tickets == 0:
                messages.info(request, f"You got the last ticket of type '{ticket_type}'!")
            
            return redirect('main:event_detail', slug=event.slug)
            
        except Exception as e:
            # Log the detailed error
            print(f"Error during registration: {e}")
            messages.error(request, "An error occurred during registration. Please try again.")
            return redirect('main:event_detail', slug=event.slug)
    
    # If GET request, redirect to event detail page
    return redirect('main:event_detail', slug=event.slug)


@user_passes_test(lambda u: u.is_staff)
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

@user_passes_test(lambda u: u.is_staff)
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

def send_registration_cancellation(registration):
    user = registration.user
    event = registration.event
    subject = f"Registration Cancelled: {event.title}"

    # Prepare context for email
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'event_url': f"{settings.SITE_URL}/events/{event.slug}/",  # adjust based on your URL pattern
        'settings': settings,
    }

    html_message = render_to_string('emails/registration_cancellation.html', context)
    
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'  # Send as HTML
    email.send()


@login_required
def cancel_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(Registration, event=event, user=request.user)
    
    # Check if registration can be cancelled
    # if not registration.can_cancel:
    #     messages.error(request, "This registration cannot be cancelled.")
    #     return redirect('main:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        # registration.status = 'cancelled'
        # registration.save()
        registration.ticket.status = 'available'
        registration.ticket.user = None
        registration.ticket.save()
        try:
            send_registration_cancellation(registration)
            registration.delete()
            messages.success(request, f"Your registration for '{event.title}' has been cancelled. A confirmation email has been sent.")
        except Exception as e:
            print(f"Your registration for '{event.title}' has been cancelled. Error sending cancellation email: {e}")
            registration.delete()
        
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

@user_passes_test(lambda u: u.is_staff)
def comments_management(request):
    # Get all events for the filter dropdown
    events = Event.objects.filter(status='published').order_by('title')
    
    # Start with all comments
    comments_queryset = Comment.objects.select_related('user', 'event', 'parent').order_by('-created_at')
    
    # Apply filters if provided
    search_query = request.GET.get('search', '')
    event_filter = request.GET.get('event', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        comments_queryset = comments_queryset.filter(
            Q(content__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if event_filter:
        comments_queryset = comments_queryset.filter(event_id=event_filter)
    
    if status_filter:
        if status_filter == 'parent':
            comments_queryset = comments_queryset.filter(parent=None)
        elif status_filter == 'replies':
            comments_queryset = comments_queryset.exclude(parent=None)
    
    # Paginate results
    paginator = Paginator(comments_queryset, 10)  # Show 10 comments per page
    page_number = request.GET.get('page', 1)
    comments_list = paginator.get_page(page_number)
    
    # Calculate stats for dashboard
    stats = {
        'total': Comment.objects.count(),
        'parent': Comment.objects.filter(parent=None).count(),
        'replies': Comment.objects.exclude(parent=None).count(),
    }
    
    context = {
        'comments_list': comments_list,
        'events': events,
        'stats': stats,
        'page': 'comments',
    }
    
    return render(request, 'comments_management.html', context)

@login_required
@permission_required('main.add_comment', raise_exception=True)
def reply_comment(request, comment_id):
    """
    Add a reply to a comment as an admin
    """
    if request.method == 'POST':
        parent_comment = get_object_or_404(Comment, id=comment_id)
        content = request.POST.get('content', '').strip()
        
        if content:
            # Create a new reply comment
            reply = Comment(
                event=parent_comment.event,
                user=request.user,
                parent=parent_comment,
                content=content
            )
            
            # Handle attachment
            if 'attachment' in request.FILES:
                attachment = request.FILES['attachment']
                # Check file size (5MB limit)
                if attachment.size > 5 * 1024 * 1024:
                    messages.error(request, "File size exceeds 5MB limit.")
                    return redirect('main:comments_management')
                
                # Check file extension
                allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                file_name = attachment.name.lower()
                if not any(file_name.endswith(ext) for ext in allowed_extensions):
                    messages.error(request, "File type not allowed. Please upload PDF, DOC, DOCX, JPG or PNG.")
                    return redirect('main:comments_management')
                
                reply.attachment = attachment
            
            reply.save()
            
            messages.success(request, "Reply posted successfully")
        else:
            messages.error(request, "Reply content cannot be empty")
    
    return redirect('main:comments_management')

@user_passes_test(lambda u: u.is_staff)
@permission_required('main.change_comment', raise_exception=True)
def edit_comment(request, comment_id):
    """
    Edit a comment as an admin
    """
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        content = request.POST.get('content', '').strip()
        
        if content:
            comment.content = content
            
            # Handle attachment removal
            if 'remove_attachment' in request.POST and comment.attachment:
                # Store the path to delete after saving
                old_attachment_path = comment.attachment.path if comment.attachment else None
                comment.attachment = None
                
                # Delete the file if it exists
                if old_attachment_path and os.path.isfile(old_attachment_path):
                    import os
                    os.remove(old_attachment_path)
            
            # Handle new attachment
            if 'attachment' in request.FILES:
                attachment = request.FILES['attachment']
                # Check file size (5MB limit)
                if attachment.size > 5 * 1024 * 1024:
                    messages.error(request, "File size exceeds 5MB limit.")
                    return redirect('main:comments_management')
                
                # Check file extension
                allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                file_name = attachment.name.lower()
                if not any(file_name.endswith(ext) for ext in allowed_extensions):
                    messages.error(request, "File type not allowed. Please upload PDF, DOC, DOCX, JPG or PNG.")
                    return redirect('main:comments_management')
                
                # If there's an existing attachment, delete it
                if comment.attachment:
                    import os
                    old_attachment_path = comment.attachment.path
                    if os.path.isfile(old_attachment_path):
                        os.remove(old_attachment_path)
                
                comment.attachment = attachment
            
            comment.save()
            
            messages.success(request, "Comment updated successfully")
        else:
            messages.error(request, "Comment content cannot be empty")
    
    return redirect('main:comments_management')


@user_passes_test(lambda u: u.is_staff)
@permission_required('main.delete_comment', raise_exception=True)
def delete_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        
        # If it's a parent comment, delete all replies too
        if comment.parent is None and comment.replies.exists():
            comment.replies.all().delete()
            
        comment.delete()
        messages.success(request, "Comment deleted successfully")
    
    return redirect('main:comments_management')

@user_passes_test(lambda u: u.is_staff)
@permission_required('main.view_comment', raise_exception=True)
def export_comments(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="comments_export.csv"'
    
    # Apply the same filters as the main view
    comments_queryset = Comment.objects.select_related('user', 'event', 'parent').order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    event_filter = request.GET.get('event', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        comments_queryset = comments_queryset.filter(
            Q(content__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if event_filter:
        comments_queryset = comments_queryset.filter(event_id=event_filter)
    
    if status_filter:
        if status_filter == 'parent':
            comments_queryset = comments_queryset.filter(parent=None)
        elif status_filter == 'replies':
            comments_queryset = comments_queryset.exclude(parent=None)
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'User', 'Email', 'Event', 'Type', 'Content', 'Parent Comment ID'])
    
    for comment in comments_queryset:
        writer.writerow([
            comment.created_at.strftime('%Y-%m-%d %H:%M'),
            comment.user.get_full_name() or comment.user.username,
            comment.user.email,
            comment.event.title,
            'Reply' if comment.parent else 'Comment',
            comment.content,
            comment.parent.id if comment.parent else '',
        ])
    
    return response

@user_passes_test(lambda u: u.is_staff)
def tickets(request):
    events = Event.objects.all().order_by('-start_date')
    tickets_queryset = Ticket.objects.select_related('event', 'user').all()
    
    search_query = request.GET.get('search', '')
    event_filter = request.GET.get('event', '')
    
    if search_query:
        tickets_queryset = tickets_queryset.filter(
            Q(ticket_id__icontains=search_query) | 
            Q(event__title__icontains=search_query)
        )
    
    if event_filter:
        tickets_queryset = tickets_queryset.filter(event__id=event_filter)
    
    paginator = Paginator(tickets_queryset, 10)
    page_number = request.GET.get('page', 1)
    tickets = paginator.get_page(page_number)
    
    stats = {
        'total_tickets': Ticket.objects.count(),
        'sold_tickets': Ticket.objects.filter(status='sold').count(),
        'available_tickets': Ticket.objects.filter(status='available').count(),
        'revenue': Ticket.objects.filter(status='sold').aggregate(Sum('price'))['price__sum'] or 0,
    }
    
    return render(request, 'tickets.html', {
        'tickets': tickets,
        'events': events,
        'stats': stats,
    })

@user_passes_test(lambda u: u.is_staff)
def create_ticket(request):
    if request.method == 'POST':
        event_id = request.POST.get('event')
        ticket_type = request.POST.get('type')
        price = request.POST.get('price')
        quantity = int(request.POST.get('quantity', 1))
        
        event = get_object_or_404(Event, id=event_id)
        
        for _ in range(quantity):
            Ticket.objects.create(
                event=event,
                type=ticket_type,
                price=price,
                status='available'
            )
        
        messages.success(request, f"{quantity} tickets created successfully.")
        return redirect('main:tickets')
    
    return redirect('main:tickets')

@user_passes_test(lambda u: u.is_staff)
def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket.delete()
    messages.success(request, "Ticket deleted successfully.")
    return redirect('main:tickets')

@user_passes_test(lambda u: u.is_staff)
def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'view_ticket.html', {'ticket': ticket})

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        ticket.type = request.POST.get('type')
        ticket.price = request.POST.get('price')
        ticket.status = request.POST.get('status')
        ticket.save()
        
        messages.success(request, "Ticket updated successfully.")
        return redirect('main:tickets')
    
    return render(request, 'edit_ticket.html', {'ticket': ticket})

def generate_ticket_for_registration(registration):
    if registration.status == 'confirmed':
        event = registration.event
        
        # Create a new ticket for the registration
        Ticket.objects.create(
            event=event,
            registration=registration,
            user=registration.user,
            type='Standard',  # Default type
            price=0.00,  # Default price
            status='sold'
        )
