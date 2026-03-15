"""
Authentication serializers.
"""
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Company, User


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'plan', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    company_id = serializers.UUIDField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_plan = serializers.CharField(source='company.plan', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'company_id', 'company_name', 'company_plan',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'full_name', 'company_id', 'company_name', 'company_plan', 'created_at', 'updated_at']


class RegisterSerializer(serializers.Serializer):
    """Register a new company + admin user together."""
    # Company fields
    company_name = serializers.CharField(max_length=255)
    plan = serializers.ChoiceField(choices=['basic', 'pro', 'enterprise'], default='basic')
    # User fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def create(self, validated_data):
        # Create company
        company = Company.objects.create(
            name=validated_data['company_name'],
            plan=validated_data['plan'],
        )
        # Create admin user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            company=company,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='admin',
            is_staff=False,
        )
        return company, user


class LoginSerializer(serializers.Serializer):
    """Login with email and password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        user = authenticate(request=self.context.get('request'), email=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs


class CreateUserSerializer(serializers.ModelSerializer):
    """Admin creates an employee in the same company."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role', 'is_active']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_role(self, value):
        # Only super_admin can create admins; regular admin can only create employees
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.role == 'admin' and value in ['super_admin', 'admin']:
                raise serializers.ValidationError('Admins can only create employee roles.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        company = request.user_company if request else None
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            company=company,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'employee'),
        )
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Allow users to update their own first/last name only."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class LogoutSerializer(serializers.Serializer):
    """Blacklist a refresh token on logout."""
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except Exception:
            raise serializers.ValidationError('Token is invalid or expired.')
