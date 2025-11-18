from django.contrib import admin

from .models import Tenant, TenantAddress, TenantAssociation


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "email", "is_active", "created_at"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "email"]


@admin.register(TenantAddress)
class TenantAddressAdmin(admin.ModelAdmin):
    list_display = ["tenant", "address_type", "city", "state", "country", "is_active"]
    list_filter = ["address_type", "is_active", "country"]
    search_fields = ["tenant__name", "city", "state"]


@admin.register(TenantAssociation)
class TenantAssociationAdmin(admin.ModelAdmin):
    list_display = ["seller", "buyer", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["seller__name", "buyer__name"]
