from django.urls import path
from .views import LoginView
from .views import create_ticket
from . import views

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("create/", create_ticket, name="create_ticket"),
    path("list/", views.ticket_list, name="ticket_list"),
    # path('ticket/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('ticket/<int:ticket_id>/update/', views.update_ticket, name='update_ticket'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path("register/", views.register_user, name="register"),
]
