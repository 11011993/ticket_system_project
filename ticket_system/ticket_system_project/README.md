# Ticket System Project

A Django-based ticket management system that allows users to create, assign, and update tickets with activity logging and notifications.

## Prerequisites

- **Python**
- **Django**
- **MySQL**
- **pip** for Python package management
- **SMTP server** for sending email notifications (e.g., Gmail, SendGrid)

## Installation and Setup

# create virtualenv
virtualenv localenv

# activate the virtualenv
source localenv/bin/activate

# install django
pip install django

# create django project
django-admin startproject ticket_system_project

# go to in project
cd ticket_system_project

# create app in project
python3 manage.py startapp ticket_app

# install mysqlclient
pip install mysqlclient

# set up the database in settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': '127.0.0.1',
        'PORT': "3306",
    }
}

# run migrate command
python manage.py migrate

# create superuser
python manage.py createsuperuser

# set up the email configuration to send mail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email'
EMAIL_HOST_PASSWORD = 'your_password'        
DEFAULT_FROM_EMAIL = 'your_email'

# start server
python manage.py runserver