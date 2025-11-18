# Generated migration for Customer, Cart and CartItem models

import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0001_initial"),
        ("products", "0001_initial"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone", models.CharField(blank=True, max_length=50, null=True)),
                ("company_name", models.CharField(blank=True, max_length=255, null=True)),
                ("tax_id", models.CharField(blank=True, max_length=100, null=True)),
                ("credit_limit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("payment_terms_days", models.IntegerField(default=30)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="customers", to="tenants.tenant"
                    ),
                ),
            ],
            options={
                "db_table": "customer",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["email"], name="customer_email_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["tenant", "email"], name="customer_tenant_email_idx"),
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "buyer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="carts",
                        to="tenants.tenant",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="carts",
                        to="commerce.customer",
                    ),
                ),
            ],
            options={
                "db_table": "cart",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["session_key", "is_active"], name="cart_session_active_idx"),
        ),
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["buyer", "is_active"], name="cart_buyer_active_idx"),
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="items", to="commerce.cart"
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="cart_items", to="products.product"
                    ),
                ),
            ],
            options={
                "db_table": "cart_item",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(fields=["cart", "product"], name="cart_item_cart_id_product_id"),
        ),
        migrations.AddField(
            model_name="lead",
            name="cart",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leads",
                to="commerce.cart",
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="customer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leads",
                to="commerce.customer",
            ),
        ),
    ]
