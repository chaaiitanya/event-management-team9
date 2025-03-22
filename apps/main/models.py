from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

class Event(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    )
    
    CATEGORY_CHOICES = (
        ('academic', 'Academic'),
        ('social', 'Social'),
        ('workshop', 'Workshop'),
        ('conference', 'Conference'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='academic')
    image = models.ImageField(upload_to='events/%Y/%m/%d/', blank=True, null=True)
    capacity = models.PositiveIntegerField(default=0)  # 0 means unlimited
    registration_deadline = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['-start_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('main:event_detail', args=[self.slug])
    
    @property
    def is_past_event(self):
        return self.end_date < timezone.now()
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def registration_open(self):
        if not self.registration_deadline:
            return self.status == 'published' and not self.is_past_event
        return self.status == 'published' and timezone.now() <= self.registration_deadline
    
    @property
    def get_abbreviated_name(self):
        """Returns the abbreviated name of the event creator."""
        full_name = self.created_by.get_full_name()
        if not full_name:
            return self.created_by.email[:2]
        
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            return f"{name_parts[0][0]}{name_parts[-1][0]}"
        return name_parts[0][:2]
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date


class Registration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    registration_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attended = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title}"
    
    @property
    def is_active(self):
        return self.status == 'confirmed'
    
    @property
    def can_cancel(self):
        return self.status in ['pending', 'confirmed'] and not self.event.is_past_event
