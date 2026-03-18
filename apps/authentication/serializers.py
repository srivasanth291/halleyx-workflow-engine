from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.authentication.models import Company, Role

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_admin', 'created_at']
        read_only_fields = ['id', 'created_at']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'plan', 'is_active', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    company_plan = serializers.ReadOnlyField()
    # Return role as full nested object so frontend can check role.is_admin
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'is_active', 'company', 'company_name', 'company_plan', 'created_at']
        read_only_fields = ['company', 'is_active', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }
    
    def create(self, validated_data):
        company = self.context['request'].user.company
        role = validated_data.get('role')
        
        # If no role provided, default to 'Employee' for this company
        if not role:
            role, _ = Role.objects.get_or_create(company=company, name='Employee', defaults={'is_admin': False})

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=role,
            company=company
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Return role as a full object so frontend isAdmin check works consistently
        role_data = None
        if user.role:
            role_data = {
                'id': str(user.role.id),
                'name': user.role.name,
                'is_admin': user.role.is_admin,
            }
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'role': role_data,
            'company_id': str(user.company.id) if user.company else None,
            'company_name': user.company_name,
            'company_plan': user.company_plan,
        }
        return data
