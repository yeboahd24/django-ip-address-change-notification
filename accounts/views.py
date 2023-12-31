from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomUserSerializer
from rest_framework.request import Request
from .models import CustomUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from accounts.tasks.login_notification import send_login_notification_email
from django.template.loader import render_to_string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.hashers import check_password
from datetime import datetime
from decouple import config
import os
import requests
from django_celery_email.settings import BASE_DIR


# get user location information
def get_location_info(self, ip_address):
    # Use an external API to get location information
    api_key = config("IPSTACK_API_KEY")
    url = f"http://api.ipstack.com/{ip_address}?access_key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        location_data = response.json()
        user_location = f"{location_data['city']}, {location_data['region_name']}, {location_data['country_name']}"
        return user_location
    except requests.exceptions.RequestException as e:
        # Handle API request errors
        print(f"Error fetching location information: {e}")
        return None


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Registration of a new user requires the following fields:",
        tags=["User Management"],
        request_body=CustomUserSerializer,
        responses={201: CustomUserSerializer(many=False)},
    )
    def post(self, request: Request) -> Response:
        data = request.data

        serializer = CustomUserSerializer(data=data)
        email = data.get("email")
        if serializer.is_valid():
            serializer.save()
            new_user = CustomUser.objects.get(email=email)
            new_user.user_ip_address = request.META.get("REMOTE_ADDR")
            if new_user.user_ip_address is None:
                new_user.user_ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
            new_user.save()

            response = {
                "status": "success",
                "message": "Account created successfully.",
                "data": serializer.data,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        bad_response = {
            "status": "error",
            "message": "User not registered",
            "data": serializer.errors,
        }
        return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Login an existing user",
        operation_description="Login of an existing user requires the following fields:",
        tags=["User Management"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User email"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User password"
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING, description="success or error"
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Login successful or User not found with this email or Incorrect password",
                    ),
                    "access": openapi.Schema(
                        type=openapi.TYPE_STRING, description="Access token"
                    ),
                    "refresh": openapi.Schema(
                        type=openapi.TYPE_STRING, description="Refresh token"
                    ),
                    "user_profile": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "status": openapi.Schema(
                                type=openapi.TYPE_STRING, description="success or error"
                            ),
                            "message": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Login successful or User not found with this email or Incorrect password",
                            ),
                            "user_id": openapi.Schema(
                                type=openapi.TYPE_STRING, description="User id"
                            ),
                            "first_name": openapi.Schema(
                                type=openapi.TYPE_STRING, description="User first name"
                            ),
                            "last_name": openapi.Schema(
                                type=openapi.TYPE_STRING, description="User last name"
                            ),
                            "email": openapi.Schema(
                                type=openapi.TYPE_STRING, description="User email"
                            ),
                            "phone_number": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="User phone number",
                            ),
                        },
                    ),
                },
            )
        },
    )
    def post(self, request: Request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        existing_user = CustomUser.objects.filter(email=email).first()
        if existing_user is None:
            bad_request_response = {
                "status": "failed",
                "message": "User not found with this email",
            }
            return Response(bad_request_response, status=status.HTTP_400_BAD_REQUEST)

        if check_password(password, existing_user.password) is False:
            bad_request_response = {"status": "failed", "message": "Incorrect password"}
            return Response(bad_request_response, status=status.HTTP_400_BAD_REQUEST)
        user_request_ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if user_request_ip_address is None:
            user_request_ip_address = request.META.get("REMOTE_ADDR")
        ip_address = user_request_ip_address

        if existing_user.user_ip_address is None:
            existing_user.user_ip_address = ip_address
            existing_user.save()

        if existing_user.user_ip_address != user_request_ip_address:
            # send email to user to notify them of login from a different location
            context = {
                "user_first_name": existing_user.first_name,
                "user_new_location": get_location_info(self, ip_address=ip_address),
                "user_new_ip_address": ip_address,
                "user_new_device": request.META.get("HTTP_USER_AGENT"),
                "formatted_time": datetime.now().strftime("%A, %B %d, %Y at %I:%M%p"),
                "change_password_link": f"http://localhost:8000/api/v1/forget-password/?email={email}",
            }

            # Render the HTML content using the template
            template_path = os.path.join(
                BASE_DIR,
                "utils",
                "templates",
                "accounts",
                "login_notification_email.html",
            )
            html_content = render_to_string(template_path, context, request=request)

            # Send the email to the user using Celery
            send_login_notification_email.delay(email, html_content)

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            if email:
                try:
                    user = CustomUser.objects.get(email=email)
                    if user:
                        user_profile_data = {
                            "status": "success",
                            "message": "Login successful",
                            "user_id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email,
                            "phone_number": user.phone_number,
                        }
                        response.data["user_profile"] = user_profile_data
                except CustomUser.DoesNotExist:
                    bad_request_response = {
                        "status": "failed",
                        "message": "User not found",
                    }
                    return Response(
                        bad_request_response, status=status.HTTP_400_BAD_REQUEST
                    )
        return response
