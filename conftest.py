"""
Global pytest fixtures for authentication and RBAC testing
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for tests"""
    return APIClient()


@pytest.fixture
def seller_tenant(db):
    """Create seller tenant"""
    return Tenant.objects.create(
        name="Test Seller",
        type="seller",
        email="seller@test.com"
    )


@pytest.fixture
def buyer_tenant(db):
    """Create buyer tenant"""
    return Tenant.objects.create(
        name="Test Buyer",
        type="buyer",
        email="buyer@test.com"
    )


@pytest.fixture
def distributor_tenant(db):
    """Create distributor tenant"""
    return Tenant.objects.create(
        name="Test Distributor",
        type="distributor",
        email="distributor@test.com"
    )


@pytest.fixture
def seller_user(db, seller_tenant):
    """Create seller user"""
    user = User.objects.create_user(
        username="seller@test.com",
        email="seller@test.com",
        password="testpass123",
        first_name="Seller",
        last_name="User"
    )
    user.tenant = seller_tenant
    user.save()
    return user


@pytest.fixture
def buyer_user(db, buyer_tenant):
    """Create buyer user"""
    user = User.objects.create_user(
        username="buyer@test.com",
        email="buyer@test.com",
        password="testpass123",
        first_name="Buyer",
        last_name="User"
    )
    user.tenant = buyer_tenant
    user.save()
    return user


@pytest.fixture
def distributor_user(db, distributor_tenant):
    """Create distributor user"""
    user = User.objects.create_user(
        username="distributor@test.com",
        email="distributor@test.com",
        password="testpass123",
        first_name="Distributor",
        last_name="User"
    )
    user.tenant = distributor_tenant
    user.save()
    return user


@pytest.fixture
def authenticated_seller_client(api_client, seller_user):
    """API client authenticated as seller"""
    api_client.force_authenticate(user=seller_user)
    return api_client


@pytest.fixture
def authenticated_buyer_client(api_client, buyer_user):
    """API client authenticated as buyer"""
    api_client.force_authenticate(user=buyer_user)
    return api_client


@pytest.fixture
def authenticated_distributor_client(api_client, distributor_user):
    """API client authenticated as distributor"""
    api_client.force_authenticate(user=distributor_user)
    return api_client


# JWT Token fixtures (if JWT is installed)
@pytest.fixture
def seller_token(seller_user):
    """Get JWT token for seller"""
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(seller_user)
        return str(refresh.access_token)
    except ImportError:
        pytest.skip("JWT not installed")


@pytest.fixture
def buyer_token(buyer_user):
    """Get JWT token for buyer"""
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(buyer_user)
        return str(refresh.access_token)
    except ImportError:
        pytest.skip("JWT not installed")


@pytest.fixture
def distributor_token(distributor_user):
    """Get JWT token for distributor"""
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(distributor_user)
        return str(refresh.access_token)
    except ImportError:
        pytest.skip("JWT not installed")
