from django import forms
from apps.main.models import Event, Registration
from django.utils.text import slugify
from django.utils import timezone
import random
import string

class EventForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'rows': 5,
            'placeholder': 'Describe the event...'
        })
    )
    
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    registration_deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 
                 'category', 'image', 'capacity', 'registration_deadline', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Event Title'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Event Location'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '0 for unlimited',
                'min': 0
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        # Check if end date is after start date
        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', 'End date must be after start date')
        
        # Check if registration deadline is before start date
        if start_date and registration_deadline and registration_deadline > start_date:
            self.add_error('registration_deadline', 'Registration deadline must be before the event start date')
        
        # Check if dates are in the past
        now = timezone.now()
        if start_date and start_date < now:
            self.add_error('start_date', 'Start date cannot be in the past')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate a unique slug from the title
        base_slug = slugify(instance.title)
        if not instance.slug:
            # Check if slug exists and append random string if it does
            if Event.objects.filter(slug=base_slug).exists():
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                instance.slug = f"{base_slug}-{random_string}"
            else:
                instance.slug = base_slug
        
        if commit:
            instance.save()
        return instance

class EventForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'rows': 5,
            'placeholder': 'Describe the event...'
        })
    )
    
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    registration_deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 
                 'category', 'image', 'capacity', 'registration_deadline', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Event Title'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Event Location'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '0 for unlimited',
                'min': 0
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        # Check if end date is after start date
        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', 'End date must be after start date')
        
        # Check if registration deadline is before start date
        if start_date and registration_deadline and registration_deadline > start_date:
            self.add_error('registration_deadline', 'Registration deadline must be before the event start date')
        
        # Only check if dates are in the past for new events
        # For existing events, we should allow editing past events
        if not self.instance.pk:  # New event
            now = timezone.now()
            if start_date and start_date < now:
                self.add_error('start_date', 'Start date cannot be in the past')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate a unique slug from the title if it doesn't exist
        # or if the title has changed
        if not instance.slug or (self.instance.pk and 
                                 self.instance.title != self.cleaned_data.get('title')):
            base_slug = slugify(instance.title)
            
            # Check if slug exists and append random string if it does
            if Event.objects.filter(slug=base_slug).exclude(pk=instance.pk).exists():
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                instance.slug = f"{base_slug}-{random_string}"
            else:
                instance.slug = base_slug
        
        if commit:
            instance.save()
        return instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Format datetime fields for the datetime-local input
        if self.instance.pk:
            for field_name in ['start_date', 'end_date', 'registration_deadline']:
                field_value = getattr(self.instance, field_name)
                if field_value:
                    # Format as YYYY-MM-DDTHH:MM
                    formatted_value = field_value.strftime('%Y-%m-%dT%H:%M')
                    self.initial[field_name] = formatted_value


class RegistrationForm(forms.ModelForm):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Any special requirements or notes for the organizers...'
        })
    )
    
    agree_to_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
        }),
        error_messages={
            'required': 'You must agree to the terms and conditions to register.'
        }
    )
    
    class Meta:
        model = Registration
        fields = ['notes']
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation can be added here if needed
        # For example, checking if the event is full
        
        return cleaned_data
