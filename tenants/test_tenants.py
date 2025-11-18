"""
Tests for tenants app - targeting 100% coverage
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import Tenant, TenantAddress, TenantAssociation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller_tenant():
    return Tenant.objects.create(name="Seller Corp", type="seller", email="seller@example.com", phone="123-456-7890")


@pytest.fixture
def buyer_tenant():
    return Tenant.objects.create(name="Buyer Inc", type="buyer", email="buyer@example.com", phone="098-765-4321")


@pytest.fixture
def distributor_tenant():
    return Tenant.objects.create(
        name="Distributor LLC", type="distributor", email="distributor@example.com", phone="555-555-5555"
    )


@pytest.fixture
def tenant_address(seller_tenant):
    return TenantAddress.objects.create(
        tenant=seller_tenant,
        address_type="office",
        address1="123 Main St",
        address2="Suite 100",
        city="New York",
        state="NY",
        zip_code="10001",
        country="USA",
    )


@pytest.fixture
def tenant_association(seller_tenant, buyer_tenant):
    import uuid

    return TenantAssociation.objects.create(seller=seller_tenant, buyer=buyer_tenant, storefront_id=uuid.uuid4())


@pytest.mark.django_db
class TestTenantModels:
    """Test tenant models for 100% coverage"""

    def test_tenant_str(self, seller_tenant):
        """Test Tenant __str__ method"""
        assert str(seller_tenant) == f"{seller_tenant.name} ({seller_tenant.get_type_display()})"

    def test_tenant_address_str(self, tenant_address):
        """Test TenantAddress __str__ method"""
        expected = f"{tenant_address.tenant.name} - {tenant_address.address_type}"
        assert str(tenant_address) == expected

    def test_tenant_association_str(self, tenant_association):
        """Test TenantAssociation __str__ method"""
        expected = f"{tenant_association.seller.name} → {tenant_association.buyer.name}"
        assert str(tenant_association) == expected

    def test_tenant_properties(self, seller_tenant, buyer_tenant, distributor_tenant):
        """Test tenant type properties"""
        assert seller_tenant.is_seller is True
        assert seller_tenant.is_buyer is False
        assert seller_tenant.is_distributor is False

        assert buyer_tenant.is_seller is False
        assert buyer_tenant.is_buyer is True
        assert buyer_tenant.is_distributor is False

        assert distributor_tenant.is_seller is False
        assert distributor_tenant.is_buyer is False
        assert distributor_tenant.is_distributor is True

    def test_tenant_creation_with_all_fields(self):
        """Test creating tenant with all fields"""
        tenant = Tenant.objects.create(
            name="Full Tenant",
            type="seller",
            email="full@example.com",
            phone="111-222-3333",
            is_active=True,
        )
        assert tenant.name == "Full Tenant"
        assert tenant.phone == "111-222-3333"
        assert tenant.is_active is True

    def test_tenant_address_creation_with_all_fields(self, seller_tenant):
        """Test creating tenant address with all fields"""
        address = TenantAddress.objects.create(
            tenant=seller_tenant,
            address_type="warehouse",
            address1="456 Storage Rd",
            address2="Building B",
            city="Los Angeles",
            state="CA",
            zip_code="90001",
            country="USA",
            is_active=True,
        )
        assert address.address_type == "warehouse"
        assert address.state == "CA"
        assert address.is_active is True

    def test_tenant_association_creation(self, seller_tenant, distributor_tenant):
        """Test creating tenant association"""
        import uuid

        storefront_id = uuid.uuid4()
        association = TenantAssociation.objects.create(
            seller=seller_tenant, buyer=distributor_tenant, storefront_id=storefront_id, is_active=True
        )
        assert association.seller == seller_tenant
        assert association.buyer == distributor_tenant
        assert association.storefront_id == storefront_id
        assert association.is_active is True


@pytest.mark.django_db
class TestTenantViews:
    """Test tenant views for 100% coverage"""

    def test_list_tenants(self, api_client, seller_tenant):
        """Test listing tenants"""
        response = api_client.get("/api/tenants/tenants/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_tenant(self, api_client, seller_tenant):
        """Test retrieving a tenant"""
        response = api_client.get(f"/api/tenants/tenants/{seller_tenant.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == seller_tenant.name

    def test_create_tenant(self, api_client):
        """Test creating a tenant"""
        data = {"name": "New Tenant", "type": "buyer", "email": "newtenant@example.com", "phone": "999-999-9999"}
        response = api_client.post("/api/tenants/tenants/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Tenant"

    def test_update_tenant(self, api_client, seller_tenant):
        """Test updating a tenant"""
        data = {"name": "Updated Seller", "type": "seller", "email": seller_tenant.email}
        response = api_client.put(f"/api/tenants/tenants/{seller_tenant.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Seller"

    def test_partial_update_tenant(self, api_client, seller_tenant):
        """Test partial update of tenant"""
        data = {"phone": "111-111-1111"}
        response = api_client.patch(f"/api/tenants/tenants/{seller_tenant.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone"] == "111-111-1111"

    def test_delete_tenant(self, api_client):
        """Test deleting a tenant"""
        tenant = Tenant.objects.create(name="Delete Me", type="buyer", email="delete@example.com")
        tenant_id = tenant.id
        response = api_client.delete(f"/api/tenants/tenants/{tenant_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tenant.objects.filter(id=tenant_id).exists()

    def test_tenant_addresses_action(self, api_client, seller_tenant, tenant_address):
        """Test custom addresses action on tenant"""
        response = api_client.get(f"/api/tenants/tenants/{seller_tenant.id}/addresses/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]["address1"] == tenant_address.address1

    def test_tenant_distributors_action_success(self, api_client, seller_tenant, distributor_tenant):
        """Test custom distributors action on seller tenant"""
        # Create association
        TenantAssociation.objects.create(seller=seller_tenant, buyer=distributor_tenant, is_active=True)

        response = api_client.get(f"/api/tenants/tenants/{seller_tenant.id}/distributors/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_tenant_distributors_action_non_seller(self, api_client, buyer_tenant):
        """Test distributors action on non-seller tenant"""
        response = api_client.get(f"/api/tenants/tenants/{buyer_tenant.id}/distributors/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only sellers have distributors" in response.data["error"]

    def test_list_tenant_addresses(self, api_client, tenant_address):
        """Test listing tenant addresses"""
        response = api_client.get("/api/tenants/addresses/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_tenant_address(self, api_client, tenant_address):
        """Test retrieving a tenant address"""
        response = api_client.get(f"/api/tenants/addresses/{tenant_address.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["address1"] == tenant_address.address1

    def test_create_tenant_address(self, api_client, seller_tenant):
        """Test creating a tenant address"""
        data = {
            "tenant": str(seller_tenant.id),
            "address_type": "billing",
            "address1": "789 Billing Ave",
            "city": "Chicago",
            "zip_code": "60601",
            "country": "USA",
        }
        response = api_client.post("/api/tenants/addresses/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["address_type"] == "billing"

    def test_update_tenant_address(self, api_client, tenant_address):
        """Test updating a tenant address"""
        data = {
            "tenant": str(tenant_address.tenant.id),
            "address_type": "warehouse",
            "address1": "999 Updated St",
            "city": "Boston",
            "zip_code": "02101",
            "country": "USA",
        }
        response = api_client.put(f"/api/tenants/addresses/{tenant_address.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["city"] == "Boston"

    def test_partial_update_tenant_address(self, api_client, tenant_address):
        """Test partial update of tenant address"""
        data = {"city": "San Francisco"}
        response = api_client.patch(f"/api/tenants/addresses/{tenant_address.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["city"] == "San Francisco"

    def test_delete_tenant_address(self, api_client, seller_tenant):
        """Test deleting a tenant address"""
        address = TenantAddress.objects.create(
            tenant=seller_tenant,
            address_type="temp",
            address1="Delete Me St",
            city="Delete City",
            zip_code="00000",
            country="USA",
        )
        address_id = address.id
        response = api_client.delete(f"/api/tenants/addresses/{address_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TenantAddress.objects.filter(id=address_id).exists()

    def test_list_tenant_associations(self, api_client, tenant_association):
        """Test listing tenant associations"""
        response = api_client.get("/api/tenants/associations/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_tenant_association(self, api_client, tenant_association):
        """Test retrieving a tenant association"""
        response = api_client.get(f"/api/tenants/associations/{tenant_association.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["seller"]) == str(tenant_association.seller.id)

    def test_create_tenant_association(self, api_client, seller_tenant, buyer_tenant):
        """Test creating a tenant association"""
        data = {"seller": str(seller_tenant.id), "buyer": str(buyer_tenant.id)}
        response = api_client.post("/api/tenants/associations/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_tenant_association(self, api_client, tenant_association, seller_tenant, distributor_tenant):
        """Test updating a tenant association"""
        data = {"seller": str(seller_tenant.id), "buyer": str(distributor_tenant.id), "is_active": False}
        response = api_client.put(f"/api/tenants/associations/{tenant_association.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_partial_update_tenant_association(self, api_client, tenant_association):
        """Test partial update of tenant association"""
        data = {"is_active": False}
        response = api_client.patch(f"/api/tenants/associations/{tenant_association.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_delete_tenant_association(self, api_client, seller_tenant, buyer_tenant):
        """Test deleting a tenant association"""
        association = TenantAssociation.objects.create(seller=seller_tenant, buyer=buyer_tenant)
        association_id = association.id
        response = api_client.delete(f"/api/tenants/associations/{association_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TenantAssociation.objects.filter(id=association_id).exists()
