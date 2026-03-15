"""
Authentication views.
"""
import logging
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Company, User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    CreateUserSerializer, UpdateProfileSerializer, LogoutSerializer,
    CompanySerializer,
)
from .permissions import IsCompanyAdmin, IsCompanyMember

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates a Company + Admin User together.
    Returns company info, user info, and JWT tokens.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='Register new company and admin user',
        operation_description='Creates a new company and an admin user simultaneously. Returns JWT tokens.',
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Registration successful', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'company': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'tokens': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )),
            400: 'Validation error',
        },
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        company, user = serializer.save()
        tokens = get_tokens_for_user(user)

        return Response({
            'company': {
                'id': str(company.id),
                'name': company.name,
                'slug': company.slug,
                'plan': company.plan,
            },
            'user': {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'full_name': user.full_name,
            },
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Authenticate with email and password. Returns JWT tokens and user details.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='Login with email and password',
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Login successful'),
            400: 'Invalid credentials',
        },
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'company_id': str(user.company.id) if user.company else None,
                'company_name': user.company.name if user.company else None,
                'company_plan': user.company.plan if user.company else None,
            },
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Logout — blacklist refresh token',
        request_body=LogoutSerializer,
        responses={205: 'Logged out successfully', 400: 'Invalid token'},
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """
    GET  /api/auth/me/ — Returns current user details
    PUT  /api/auth/me/ — Update own profile (name only)
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Get current user profile',
        responses={200: UserSerializer},
        tags=['Authentication'],
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='Update own profile (name only)',
        request_body=UpdateProfileSerializer,
        responses={200: UserSerializer},
        tags=['Authentication'],
    )
    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/auth/users/ — List all users in same company
    POST /api/auth/users/ — Admin creates employee in same company
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return User.objects.filter(company=user.company)
        return User.objects.none()

    @swagger_auto_schema(
        operation_summary='List users in company',
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description='Filter by role', type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description='Search by name/email', type=openapi.TYPE_STRING),
        ],
        tags=['Users'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Create employee in company',
        request_body=CreateUserSerializer,
        tags=['Users'],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
