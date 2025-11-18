"""
Tenant models for multi-tenant architecture
"""

from django.db import models
from django.core.validators import EmailValidator
import uuid


class TenantType(models.TextChoices):
    SELLER = "seller", "Seller"
    BUYER = "buyer", "Buyer"
    DISTRIBUTOR = "distributor", "Distributor"


class Tenant(models.Model):
    """Multi-tenant company/organization"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TenantType.choices)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    @property
    def is_seller(self):
        return self.type == TenantType.SELLER

    @property
    def is_buyer(self):
        return self.type == TenantType.BUYER

    @property
    def is_distributor(self):
        return self.type == TenantType.DISTRIBUTOR


class TenantAddress(models.Model):
    """Address for tenant (warehouse, headquarters, etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=50)  # 'warehouse', 'headquarters', 'sold_to'
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_address"
        ordering = ["tenant", "address_type"]

    def __str__(self):
        return f"{self.tenant.name} - {self.address_type}"


class TenantAssociation(models.Model):
    """Association between sellers and buyers (through distributors)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="buyer_associations")
    buyer = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="seller_associations")
    storefront_id = models.UUIDField(blank=True, null=True)  # For future storefront support
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_association"
        unique_together = [["seller", "buyer", "storefront_id"]]

    def __str__(self):
        return f"{self.seller.name} → {self.buyer.name}"
