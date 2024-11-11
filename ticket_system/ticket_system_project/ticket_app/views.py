from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import View
from .forms import TicketForm, EmailAuthenticationForm, CommentForm, TicketStatusForm, UserRegistrationForm
from .models import Ticket, TicketAssignment, Activity, Notification
from django.core.mail import send_mail 
from django.contrib import messages
from django.db.models import Q
from django.db.models import Prefetch
import logging

class LoginView(View):
    template_name = "ticket_app/login.html"

    def get(self, request):
        form = EmailAuthenticationForm()
        logging.warning("Comment form is invalid2222222222: %s", form.errors)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = EmailAuthenticationForm(request, data=request.POST)
        logging.warning("Comment form is invalid1111: %s", form.errors)
        if form.is_valid():
            login(request, form.get_user())
            print("&&&&&&&&&&&&&&&&&&&&7")
            return redirect("ticket_list")
        else:
            logging.warning("Login form is invalid: %s", form.errors)
        return render(request, self.template_name, {"form": form})
    
@login_required
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creator = request.user  # Set the creator to the logged-in user
            ticket.save()

            assigned_users = form.cleaned_data["assigned_users"]
            for user in assigned_users:
                TicketAssignment.objects.create(ticket=ticket, user=user)
                send_mail(
                    subject=f"New Ticket Assigned: {ticket.title}",
                    message=f"Hello,\n\nYou have been assigned to a new ticket:\n\nTitle: {ticket.title}\nDescription: {ticket.description}\n\nPlease log in to view and manage the ticket.",
                    from_email='ganshyamnagar11@gmail.com',  # Uses DEFAULT_FROM_EMAIL in settings
                    recipient_list=[user.email],
                )

            return redirect("ticket_list")  # Redirect to a list view or homepage after creation
    else:
        form = TicketForm()
    return render(request, "ticket_app/create_ticket.html", {"form": form})

@login_required
def ticket_list(request):
    # tickets = Ticket.objects.all()
    user = request.user
    # tickets = Ticket.objects.filter(
    #     Q(creator=user) | Q(assignments__user=user)
    # ).distinct()
    tickets = Ticket.objects.prefetch_related(
    Prefetch('assignments', queryset=TicketAssignment.objects.select_related('user')),
    Prefetch('activities', queryset=Activity.objects.filter(activity_type="comment").order_by('-timestamp'))
    ).filter(
        Q(creator=user) | Q(assignments__user=user)
    ).distinct()
    return render(request, "ticket_app/ticket_list.html", {"tickets": tickets})

def send_activity_notifications(ticket, activity):
    # Gather the email addresses of the ticket creator and assigned users
    recipient_list = {ticket.creator.email} if ticket.creator.email else set()
    assigned_users = TicketAssignment.objects.filter(ticket=ticket).select_related("user")
    for assignment in assigned_users:
        if assignment.user.email:
            recipient_list.add(assignment.user.email)

    # Send the email notification
    message = (
        f"Hello,\n\nA new activity was added to the ticket '{ticket.title}':\n\n"
        f"Activity Type: {activity.activity_type}\n"
        f"Performed by: {activity.user.email}\n"
        f"Comment: {activity.comment or 'N/A'}\n"
        f"Status: {activity.status or 'N/A'}\n\n"
        "Please log in to view the details."
        )

    if recipient_list:
        send_mail(
            subject=f"New Activity on Ticket: {ticket.title}",
            message = message,
            from_email=None,  # Use the default email from settings
            recipient_list=list(recipient_list),
        )
        Notification.objects.create(user=ticket.creator, ticket=ticket, message=message)


@login_required
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if the user is the creator or an assigned user
    is_creator = request.user == ticket.creator
    is_assigned = TicketAssignment.objects.filter(ticket=ticket, user=request.user).exists()

    if not (is_creator or is_assigned):
        messages.error(request, "You do not have permission to update this ticket.")
        return redirect("ticket_detail", ticket_id=ticket.id)

    comment_form = CommentForm()
    status_form = TicketStatusForm()

    if request.method == "POST":
        # First, check if we're updating a comment or the status
        if "submit_comment" in request.POST:
            # Handle comment form submission
            form = CommentForm(request.POST)
            logging.info("POST data: %s", request.POST)
            if form.is_valid():
                comment = form.cleaned_data["comment"]
                # comment = "Temporary test comment"
                activity = Activity.objects.create(
                    ticket=ticket,
                    user=request.user,
                    activity_type="comment",
                    comment=comment,
                )
                logging.info("Comment added successfully")
                send_activity_notifications(ticket, activity)
                return redirect("ticket_detail", ticket_id=ticket.id)
            else:
                logging.warning("Comment form is invalid: %s", form.errors)
        elif "status" in request.POST:
            # Handle ticket status form submission
            form = TicketStatusForm(request.POST, instance=ticket)
            if form.is_valid():
                previous_status = ticket.status
                form.save()

                # Log the activity only if the status has changed
                if previous_status != ticket.status:
                    activity = Activity.objects.create(
                        ticket=ticket,
                        user=request.user,
                        activity_type="status_change",
                        status=ticket.get_status_display(),
                    )
                    send_activity_notifications(ticket, activity)

                return redirect("ticket_detail", ticket_id=ticket.id)
    else:
        # If it's a GET request, render both forms
        comment_form = CommentForm()
        status_form = TicketStatusForm(instance=ticket)

    return render(request, "ticket_app/update_ticket_status.html", {
        "comment_form": comment_form,
        "status_form": status_form,
        "ticket": ticket,
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    assigned_users = TicketAssignment.objects.filter(ticket=ticket)
    assigned_user_ids = assigned_users.values_list('user__id', flat=True)

    activities = Activity.objects.filter(ticket=ticket).order_by('-timestamp')

    return render(request, "ticket_app/single_ticket_detail.html", {
        "ticket": ticket,
        "assigned_users": assigned_users,
        "assigned_user_ids": assigned_user_ids,
        "activities": activities,
    })

def register_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)  # Log the user in after successful registration
            return redirect("home")  # Redirect to home or a welcome page
    else:
        form = UserRegistrationForm()
    return render(request, "ticket_app/register.html", {"form": form})
