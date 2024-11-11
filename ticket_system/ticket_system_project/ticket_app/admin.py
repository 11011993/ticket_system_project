from django.contrib import admin
from .models import Ticket, TicketAssignment, Activity
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

class TicketAssignmentInline(admin.TabularInline):
    model = TicketAssignment
    extra = 1
    verbose_name = "Assigned User"
    verbose_name_plural = "Assigned Users"

class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0
    readonly_fields = ('user', 'activity_type', 'comment', 'status', 'timestamp')
    can_delete = False
    verbose_name = "Activity Log"
    verbose_name_plural = "Activity Logs"

class TicketAdminForm(forms.ModelForm):
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Users"
    )

    class Meta:
        model = Ticket
        fields = ["title", "description", "priority", "status", "assigned_users"]

class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = ("title", "priority", "status", "creator", "created_at")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("title", "description", "creator__email")
    inlines = [TicketAssignmentInline, ActivityInline]

    def get_queryset(self, request):
        """Limit tickets to those created by or assigned to the current user."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers see all tickets

        # Filter tickets to those where the user is the creator or assigned
        return qs.filter(
            Ticket.Q(creator=request.user) | Ticket.Q(ticketassignment__user=request.user)
        ).distinct()

    def save_model(self, request, obj, form, change):
        """Override save to handle ticket assignments."""
        if not change or not obj.creator:  # Only set creator for new tickets
            obj.creator = request.user
        super().save_model(request, obj, form, change)
        
        # Handle user assignments
        assigned_users = form.cleaned_data.get("assigned_users", [])
        # Clear previous assignments to avoid duplicates
        TicketAssignment.objects.filter(ticket=obj).delete()
        # Assign new users
        for user in assigned_users:
            TicketAssignment.objects.create(ticket=obj, user=user)

class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('email','first_name', 'last_name')  # Only email is required for user creation

    def clean_password2(self):
        # Ensure both passwords match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields must match.")

        return password2

class CustomUserAdmin(UserAdmin):
    # You can customize the User Admin fields here
    model = User
    list_display = ('email', 'first_name', 'last_name','is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email','first_name', 'last_name')
    ordering = ('email',)

    add_form = CustomUserCreationForm  # Specify the form to use for adding users
    add_fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name','password1', 'password2'),
        }),
    )

    fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name','password', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    # You can exclude fields like 'username', 'first_name', 'last_name', etc. if not present in the model
    exclude = ('username', 'date_joined')

# Register the custom UserAdmin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Ticket, TicketAdmin)
