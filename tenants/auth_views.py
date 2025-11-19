"""
Authentication views for JWT-based auth
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate

# Try to import JWT, but make it optional
try:
    from rest_framework_simplejwt.tokens import RefreshToken
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint - returns JWT tokens

    POST /api/auth/login/
    {
        "username": "user@example.com",
        "password": "password123"
    }

    Returns:
    {
        "access": "eyJ0eXAiOiJKV1Q...",
        "refresh": "eyJ0eXAiOiJKV1Q...",
        "user": {
            "id": 1,
            "username": "user@example.com",
            "tenant": {
                "id": "uuid",
                "name": "Tenant Name",
                "type": "seller"
            }
        }
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Build response with user info
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }

    # Add tenant info if available
    if hasattr(user, 'tenant'):
        user_data['tenant'] = {
            'id': str(user.tenant.id),
            'name': user.tenant.name,
            'type': user.tenant.type,
        }

    response_data = {'user': user_data}

    # Generate JWT tokens if available
    if JWT_AVAILABLE:
        refresh = RefreshToken.for_user(user)
        response_data['access'] = str(refresh.access_token)
        response_data['refresh'] = str(refresh)

    return Response(response_data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    User registration endpoint

    POST /api/auth/register/
    {
        "username": "user@example.com",
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "tenant_id": "uuid"  // Optional
    }
    """
    from django.contrib.auth import get_user_model
    from tenants.models import Tenant

    User = get_user_model()

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response(
            {'error': 'Please provide username, email and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', '')
    )

    # Associate with tenant if provided
    tenant_id = request.data.get('tenant_id')
    if tenant_id:
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            user.tenant = tenant
            user.save()
        except Tenant.DoesNotExist:
            pass

    response_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    }

    # Generate JWT tokens if available
    if JWT_AVAILABLE:
        refresh = RefreshToken.for_user(user)
        response_data['access'] = str(refresh.access_token)
        response_data['refresh'] = str(refresh)

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def me(request):
    """
    Get current user info

    GET /api/auth/me/
    Headers: Authorization: Bearer <token>
    """
    user = request.user

    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }

    # Add tenant info if available
    if hasattr(user, 'tenant'):
        user_data['tenant'] = {
            'id': str(user.tenant.id),
            'name': user.tenant.name,
            'type': user.tenant.type,
            'email': user.tenant.email,
        }

    return Response(user_data)
