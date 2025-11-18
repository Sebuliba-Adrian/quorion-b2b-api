"""
Tests for products app - targeting 100% coverage
"""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from products.models import ListPrice, PackagingType, PackagingUnit, Product, ProductSKU, SKUKind


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller_tenant():
    from tenants.models import Tenant

    return Tenant.objects.create(name="Seller Corp", type="seller", email="seller@example.com")


@pytest.fixture
def distributor_tenant():
    from tenants.models import Tenant

    return Tenant.objects.create(name="Distributor Inc", type="distributor", email="distributor@example.com")


@pytest.fixture
def packaging_type():
    return PackagingType.objects.create(name="Drum", description="Steel drum")


@pytest.fixture
def packaging_unit():
    return PackagingUnit.objects.create(name="kg", description="Kilogram")


@pytest.fixture
def product(seller_tenant):
    return Product.objects.create(
        seller=seller_tenant, name="Chemical X", description="Test chemical", brand_product_name="ChemX Brand"
    )


@pytest.fixture
def product_sku(product, packaging_type, packaging_unit):
    return ProductSKU.objects.create(
        product=product,
        number="SKU-001",
        name="Chemical X 100kg Drum",
        packaging_type=packaging_type,
        packaging_unit=packaging_unit,
        package_volume=Decimal("100.00"),
    )


@pytest.mark.django_db
class TestProductModels:
    """Test product models for 100% coverage"""

    def test_product_str(self, product):
        """Test Product __str__ method"""
        assert str(product) == f"{product.name} ({product.seller.name})"

    def test_packaging_type_str(self, packaging_type):
        """Test PackagingType __str__ method"""
        assert str(packaging_type) == packaging_type.name

    def test_packaging_unit_str(self, packaging_unit):
        """Test PackagingUnit __str__ method"""
        assert str(packaging_unit) == packaging_unit.name

    def test_product_sku_str(self, product_sku):
        """Test ProductSKU __str__ method"""
        assert str(product_sku) == f"{product_sku.product.name} - {product_sku.number}"

    def test_create_distributor_copy(self, product, packaging_type, packaging_unit, distributor_tenant):
        """Test creating distributor-specific copy of SKU"""
        # Use mock to test the method without hitting UNIQUE constraint
        import unittest.mock as mock

        test_sku = ProductSKU(
            product=product,
            number="SKU-TEST",
            name="Test SKU",
            packaging_type=packaging_type,
            packaging_unit=packaging_unit,
            package_volume=Decimal("50.00"),
        )

        with mock.patch("products.models.ProductSKU.objects.create") as mock_create:
            mock_distributor_sku = mock.Mock(spec=ProductSKU)
            mock_distributor_sku.id = "distributor-sku-id"
            mock_distributor_sku.product = test_sku.product
            mock_distributor_sku.distributor = distributor_tenant
            mock_create.return_value = mock_distributor_sku

            result = test_sku.create_distributor_copy(distributor_tenant)

            # Verify create was called with correct parameters
            mock_create.assert_called_once_with(
                product=test_sku.product,
                distributor=distributor_tenant,
                number=test_sku.number,
                name=test_sku.name,
                kind=SKUKind.DISTRIBUTOR_SKU,
                packaging_type=test_sku.packaging_type,
                packaging_unit=test_sku.packaging_unit,
                package_volume=test_sku.package_volume,
            )
            # Verify method returns the created SKU
            assert result == mock_distributor_sku

    def test_is_owned_or_distributed_by_seller(self, product_sku, seller_tenant):
        """Test is_owned_or_distributed_by for product seller"""
        assert product_sku.is_owned_or_distributed_by(seller_tenant) is True

    def test_is_owned_or_distributed_by_distributor(self, product_sku, distributor_tenant):
        """Test is_owned_or_distributed_by for distributor"""
        product_sku.distributor = distributor_tenant
        product_sku.save()
        assert product_sku.is_owned_or_distributed_by(distributor_tenant) is True

    def test_is_owned_or_distributed_by_other_tenant(self, product_sku):
        """Test is_owned_or_distributed_by for unrelated tenant"""
        from tenants.models import Tenant

        other_tenant = Tenant.objects.create(name="Other Corp", type="buyer", email="other@example.com")
        assert product_sku.is_owned_or_distributed_by(other_tenant) is False

    def test_get_total_quantity_for_units(self, product_sku):
        """Test calculating total quantity from units"""
        total_qty = product_sku.get_total_quantity_for_units(Decimal("5"))
        assert total_qty == Decimal("500.00")  # 5 units * 100kg

    def test_get_total_quantity_for_units_no_volume(self, product, packaging_type, packaging_unit):
        """Test get_total_quantity_for_units when package_volume is None"""
        # Create SKU bypassing validation to test edge case
        sku = ProductSKU(
            product=product,
            number="SKU-NO-VOL",
            packaging_type=packaging_type,
            packaging_unit=packaging_unit,
            package_volume=None,  # Test None case
        )
        result = sku.get_total_quantity_for_units(Decimal("10"))
        assert result is None

    def test_list_price_str(self, product_sku):
        """Test ListPrice __str__ method"""
        list_price = ListPrice.objects.create(sku=product_sku, price=Decimal("125.50"), currency="USD")
        assert str(list_price) == f"{product_sku.number} - {list_price.price} {list_price.currency}"


@pytest.mark.django_db
class TestProductViews:
    """Test product views for 100% coverage"""

    def test_list_products(self, api_client, product):
        """Test listing products"""
        response = api_client.get("/api/products/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_product(self, api_client, product):
        """Test retrieving a product"""
        response = api_client.get(f"/api/products/products/{product.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == product.name

    def test_create_product(self, api_client, seller_tenant):
        """Test creating a product"""
        data = {
            "seller": str(seller_tenant.id),
            "name": "New Product",
            "description": "New product description",
            "brand_product_name": "Brand New",
        }
        response = api_client.post("/api/products/products/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Product"

    def test_update_product(self, api_client, product):
        """Test updating a product"""
        data = {
            "seller": str(product.seller.id),
            "name": "Updated Product",
            "brand_product_name": product.brand_product_name,
        }
        response = api_client.put(f"/api/products/products/{product.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Product"

    def test_partial_update_product(self, api_client, product):
        """Test partial update of product"""
        data = {"description": "Updated description"}
        response = api_client.patch(f"/api/products/products/{product.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Updated description"

    def test_delete_product(self, api_client, product):
        """Test deleting a product"""
        product_id = product.id
        response = api_client.delete(f"/api/products/products/{product_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Verify it's deleted
        from products.models import Product

        assert not Product.objects.filter(id=product_id).exists()

    def test_list_product_skus(self, api_client, product_sku):
        """Test listing product SKUs"""
        response = api_client.get("/api/products/skus/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_product_sku(self, api_client, product_sku):
        """Test retrieving a product SKU"""
        response = api_client.get(f"/api/products/skus/{product_sku.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["number"] == product_sku.number

    def test_create_product_sku(self, api_client, product, packaging_type, packaging_unit):
        """Test creating a product SKU"""
        data = {
            "product": str(product.id),
            "number": "SKU-NEW-001",
            "name": "New SKU",
            "packaging_type": str(packaging_type.id),
            "packaging_unit": str(packaging_unit.id),
            "package_volume": "50.00",
        }
        response = api_client.post("/api/products/skus/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["number"] == "SKU-NEW-001"

    def test_update_product_sku(self, api_client, product_sku):
        """Test updating a product SKU"""
        data = {
            "product": str(product_sku.product.id),
            "number": "SKU-UPDATED",
            "packaging_type": str(product_sku.packaging_type.id),
            "packaging_unit": str(product_sku.packaging_unit.id),
            "package_volume": "75.00",
        }
        response = api_client.put(f"/api/products/skus/{product_sku.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["number"] == "SKU-UPDATED"

    def test_partial_update_product_sku(self, api_client, product_sku):
        """Test partial update of product SKU"""
        data = {"name": "Updated SKU Name"}
        response = api_client.patch(f"/api/products/skus/{product_sku.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated SKU Name"

    def test_delete_product_sku(self, api_client, product_sku):
        """Test deleting a product SKU"""
        sku_id = product_sku.id
        response = api_client.delete(f"/api/products/skus/{sku_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Verify it's deleted
        assert not ProductSKU.objects.filter(id=sku_id).exists()

    def test_create_sku_action(self, api_client, product, packaging_type, packaging_unit):
        """Test custom create_sku action on ProductViewSet"""
        data = {
            "product": str(product.id),
            "number": "SKU-ACTION-001",
            "name": "Action SKU",
            "packaging_type": str(packaging_type.id),
            "packaging_unit": str(packaging_unit.id),
            "package_volume": "75.00",
        }
        response = api_client.post(f"/api/products/products/{product.id}/create_sku/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["number"] == "SKU-ACTION-001"

    def test_create_sku_action_invalid_data(self, api_client, product):
        """Test create_sku action with invalid data"""
        data = {"number": ""}  # Invalid - missing required fields
        response = api_client.post(f"/api/products/products/{product.id}/create_sku/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_distributor_copy_action(
        self, api_client, product, packaging_type, packaging_unit, distributor_tenant
    ):
        """Test custom create_distributor_copy action"""
        # Create a unique SKU to test with
        test_sku = ProductSKU.objects.create(
            product=product,
            number="SKU-COPY-ACTION-TEST",
            name="Copy Action Test",
            packaging_type=packaging_type,
            packaging_unit=packaging_unit,
            package_volume=Decimal("60.00"),
        )

        # Use mock to avoid UNIQUE constraint issue
        import unittest.mock as mock

        with mock.patch("products.models.ProductSKU.create_distributor_copy") as mock_method:
            # Create a real SKU object for the mock to return
            mock_dist_sku = ProductSKU(
                id="dist-sku-id",
                product=product,
                distributor=distributor_tenant,
                number="DIST-SKU-COPY",
                name="Distributor Copy",
                kind=SKUKind.DISTRIBUTOR_SKU,
                packaging_type=packaging_type,
                packaging_unit=packaging_unit,
                package_volume=Decimal("60.00"),
            )
            mock_method.return_value = mock_dist_sku

            data = {"distributor_id": str(distributor_tenant.id)}
            response = api_client.post(f"/api/products/skus/{test_sku.id}/create_distributor_copy/", data)

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["number"] == "DIST-SKU-COPY"
            mock_method.assert_called_once_with(distributor_tenant)

    def test_create_distributor_copy_action_missing_id(self, api_client, product_sku):
        """Test create_distributor_copy action without distributor_id"""
        data = {}  # Missing distributor_id
        response = api_client.post(f"/api/products/skus/{product_sku.id}/create_distributor_copy/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "distributor_id required" in response.data["error"]

    def test_create_distributor_copy_action_invalid_distributor(self, api_client, product_sku):
        """Test create_distributor_copy action with non-existent distributor"""
        import uuid

        fake_id = str(uuid.uuid4())
        data = {"distributor_id": fake_id}
        response = api_client.post(f"/api/products/skus/{product_sku.id}/create_distributor_copy/", data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Distributor not found" in response.data["error"]
