# Django Celery Email Login

This project focuses on enhancing the security of a Django Rest Framework application by implementing IP address change detection using Celery for scheduled email notifications. By following these steps, you'll be able to notify users whenever their IP address during login differs from the one used during sign-up.

## Overview

Detecting changes in a user's IP address is crucial for security. This guide provides a solution to automatically send email notifications to users whenever such changes occur, adding an extra layer of protection to your Django application. The process is facilitated by Celery, which schedules the email notification task.

## Getting Started

### Prerequisites

Before diving into the implementation, ensure the following prerequisites are met:

- Python 3.x
- Redis server
- Django
- Celery

### Setup

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Perform database migrations and start the application:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

4. In a separate terminal, run Celery:

   ```bash
   celery -A utils.celery_config:app worker -l info
   ```

Now, your Django application is set up with the necessary dependencies and Celery for IP address change detection.

## Acknowledgments

This implementation ensures improved security within your Django Rest Framework application. The utilization of Celery provides a reliable and scheduled approach to handle email notifications, notifying users promptly about IP address changes during login. Enhance the security of your application with this straightforward yet powerful solution.# django-ip-address-change-notification
