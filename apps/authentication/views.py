from rest_framework import viewsets, permissions, status, views, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from apps.authentication.serializers import UserSerializer, UserCreateSerializer, CustomTokenObtainPairSerializer, RoleSerializer
from apps.authentication.models import Role
from apps.authentication.permissions import IsCompanyAdmin
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data={'first_name': request.data.get('first_name', user.first_name), 'last_name': request.data.get('last_name', user.last_name)}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsCompanyAdmin]

    def get_queryset(self):
        return Role.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCompanyAdmin]

    def get_queryset(self):
        queryset = User.objects.filter(company=self.request.user.company)
        role = self.request.query_params.get('role', None)
        search = self.request.query_params.get('search', None)
        if role:
            queryset = queryset.filter(role=role)
        if search:
            queryset = queryset.filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search))
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if 'role' in request.data:
            role_id = request.data['role']
            try:
                role = Role.objects.get(id=role_id, company=self.request.user.company)
                user.role = role
                user.save()
            except Role.DoesNotExist:
                return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle other fields via partial update if needed, but for now just role
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_200_OK)
