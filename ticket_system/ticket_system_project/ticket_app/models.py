from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.date_joined = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    username = models.CharField(max_length=30, blank=True, null=True)  # Optional username field
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def has_module_perms(self, app_label):
        return True
    
class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    # @property
    # def assigned_users(self):
    #     """Returns a queryset of users assigned to this ticket."""
    #     return self.ticket_assignments.select_related('user').all().values_list('user', flat=True)

    @property
    def assigned_users(self):
        """Returns a list of user emails assigned to this ticket."""
        return [assignment.user.email for assignment in self.assignments.all()]


    
class TicketAssignment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ticket_assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} assigned to {self.ticket.title}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ticket', 'user'], name='unique_ticket_assignment')
        ]
    
class Activity(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User who performed the activity
    timestamp = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(max_length=50)  # E.g., "status_change", "comment"
    comment = models.TextField(blank=True, null=True)  # Optional field for comments
    status = models.CharField(max_length=20, blank=True, null=True)  # Optional field for status updates

    def __str__(self):
        return f"{self.activity_type} by {self.user.username} on {self.ticket.title}"
    
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.user.email} - Ticket: {self.ticket.title}"

    class Meta:
        ordering = ['-timestamp']
