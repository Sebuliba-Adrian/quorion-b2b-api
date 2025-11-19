"""
Custom permissions for tenant-based RBAC
"""
from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """
    Require authentication for all requests
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsTenantUser(permissions.BasePermission):
    """
    User must be associated with a tenant
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'tenant')
        )


class IsSeller(permissions.BasePermission):
    """
    User's tenant must be of type 'seller'
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'tenant') and
            request.user.tenant.type == 'seller'
        )


class IsBuyer(permissions.BasePermission):
    """
    User's tenant must be of type 'buyer'
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'tenant') and
            request.user.tenant.type == 'buyer'
        )


class IsDistributor(permissions.BasePermission):
    """
    User's tenant must be of type 'distributor'
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'tenant') and
            request.user.tenant.type == 'distributor'
        )


class IsSellerOrDistributor(permissions.BasePermission):
    """
    User's tenant must be seller or distributor
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'tenant') and
            request.user.tenant.type in ['seller', 'distributor']
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit
    Read permissions for all authenticated users
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS) for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions only for owner
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        if hasattr(obj, 'seller'):
            return obj.seller == request.user.tenant
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user.tenant

        return False


class IsTenantOwner(permissions.BasePermission):
    """
    Object-level permission: User's tenant must own the object
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        # Check various possible owner fields
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        if hasattr(obj, 'seller'):
            return obj.seller == request.user.tenant
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user.tenant
        if hasattr(obj, 'owner'):
            return obj.owner == request.user.tenant

        return False


class IsSellerOfProduct(permissions.BasePermission):
    """
    User's tenant must be the seller of the product
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        # For products
        if hasattr(obj, 'seller'):
            return obj.seller == request.user.tenant

        # For product-related objects (images, variants, etc)
        if hasattr(obj, 'product') and hasattr(obj.product, 'seller'):
            return obj.product.seller == request.user.tenant

        return False


class IsBuyerOrSeller(permissions.BasePermission):
    """
    User must be either the buyer or seller of the object
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        user_tenant = request.user.tenant

        if hasattr(obj, 'buyer') and obj.buyer == user_tenant:
            return True
        if hasattr(obj, 'seller') and obj.seller == user_tenant:
            return True

        return False


class CanAccessOrder(permissions.BasePermission):
    """
    Buyer or seller can access order
    """
    def has_permission(self, request, view):
        # Allow authenticated users to list/create orders
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        user_tenant = request.user.tenant

        # Check if user is buyer or seller of the order
        return (
            (hasattr(obj, 'buyer') and obj.buyer == user_tenant) or
            (hasattr(obj, 'seller') and obj.seller == user_tenant)
        )


class CanAccessQuote(permissions.BasePermission):
    """
    Buyer or seller can access quote
    """
    def has_permission(self, request, view):
        # Allow authenticated users to list/create quotes
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        user_tenant = request.user.tenant

        # Check if user is buyer or seller of the quote
        return (
            (hasattr(obj, 'buyer') and obj.buyer == user_tenant) or
            (hasattr(obj, 'seller') and obj.seller == user_tenant)
        )


class CanAccessLead(permissions.BasePermission):
    """
    Only seller can access their leads
    """
    def has_permission(self, request, view):
        # Allow authenticated users to list/create leads
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, 'tenant'):
            return False

        # Only seller who received the lead can access it
        return hasattr(obj, 'seller') and obj.seller == request.user.tenant


class ReadOnly(permissions.BasePermission):
    """
    Read-only access for authenticated users
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.method in permissions.SAFE_METHODS
        )
