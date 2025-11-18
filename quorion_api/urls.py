"""
URL configuration for quorion_api project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/tenants/", include("tenants.urls")),
    path("api/products/", include("products.urls")),
    path("api/commerce/", include("commerce.urls")),
]
