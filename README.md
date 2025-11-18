# Quorion B2B API

[![CI/CD](https://github.com/Sebuliba-Adrian/quorion-b2b-api/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/Sebuliba-Adrian/quorion-b2b-api/actions)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen.svg)](https://github.com/Sebuliba-Adrian/quorion-b2b-api)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2.8-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-153%20passed-success)](https://github.com/Sebuliba-Adrian/quorion-b2b-api/actions)
[![CodeQL](https://github.com/Sebuliba-Adrian/quorion-b2b-api/workflows/CodeQL%20Analysis/badge.svg)](https://github.com/Sebuliba-Adrian/quorion-b2b-api/security/code-scanning)

A fully functional Django REST API for B2B distributor buyer-seller negotiation system. This MVP covers the complete transaction lifecycle from lead generation through price negotiation, order fulfillment, and shipping.

**🎯 98% Test Coverage | ✅ 153 Tests Passing | 🚀 Production Ready**

## Features

### ✅ Complete Transaction Lifecycle
- **Shopping Cart**: Full-featured cart with add/remove/update items, soft delete, cart-to-lead conversion
- **Lead Management**: Create, forward to distributors, accept/reject
- **Quote Negotiation**: Multi-step price negotiation with state machine
- **Order Processing**: Full order fulfillment workflow
- **Shipping**: Shipment advice and tracking
- **Price Tiers**: Volume-based pricing with buyer-specific rates

### ✅ State Machines
- **Lead State Machine**: `no_lead → new → converted/forwarded → accepted/rejected`
- **Quote State Machine**: `no_request → new → requested → responded → accepted`
- **Order State Machine**: `no_order → new → accepted → in_progress → invoiced → shipped → completed`

### ✅ Multi-Tenant Architecture
- **Tenant Types**: Seller, Buyer, Distributor
- **Tenant Associations**: Manage relationships between tenants
- **Distributor Integration**: Forward leads, create distributor SKUs

### ✅ Products & SKUs
- **Product Management**: Create products with multiple SKUs
- **SKU Types**: Product SKU, Distributor SKU, Buyer SKU
- **Packaging**: Packaging types and units
- **Price Tiers**: Volume-based pricing per buyer/destination

## Installation

### Prerequisites
- Python 3.12+
- Virtual environment (recommended)

### Setup

1. **Clone/Navigate to project directory**
```bash
cd quorion-b2b-api
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create superuser (optional, for admin access)**
```bash
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Shopping Cart
- `POST /api/commerce/carts/` - Create a new cart
- `GET /api/commerce/carts/` - List all carts
- `GET /api/commerce/carts/{id}/` - Get cart details with items and totals
- `PATCH /api/commerce/carts/{id}/` - Update cart
- `DELETE /api/commerce/carts/{id}/` - Delete cart
- `POST /api/commerce/carts/{id}/add_item/` - Add or update item in cart
- `POST /api/commerce/carts/{id}/remove_item/` - Remove item from cart (soft delete)
- `POST /api/commerce/carts/{id}/clear/` - Clear all items from cart
- `POST /api/commerce/carts/{id}/convert_to_lead/` - Convert cart to lead

### Tenants
- `GET/POST /api/tenants/tenants/` - List/create tenants
- `GET/PUT/PATCH/DELETE /api/tenants/tenants/{id}/` - Tenant details
- `GET /api/tenants/tenants/{id}/addresses/` - Get tenant addresses
- `GET /api/tenants/tenants/{id}/distributors/` - Get distributors for seller
- `GET/POST /api/tenants/addresses/` - Manage addresses
- `GET/POST /api/tenants/associations/` - Manage tenant associations

### Products
- `GET/POST /api/products/products/` - List/create products
- `GET/PUT/PATCH/DELETE /api/products/products/{id}/` - Product details
- `POST /api/products/products/{id}/create_sku/` - Create SKU for product
- `GET/POST /api/products/skus/` - Manage SKUs
- `POST /api/products/skus/{id}/create_distributor_copy/` - Create distributor SKU copy
- `GET/POST /api/products/packaging-types/` - Manage packaging types
- `GET/POST /api/products/packaging-units/` - Manage packaging units
- `GET/POST /api/products/list-prices/` - Manage list prices

### Commerce - Leads
- `GET/POST /api/commerce/leads/` - List/create leads
- `POST /api/commerce/leads/{id}/create_lead/` - Create new lead
- `POST /api/commerce/leads/{id}/convert/` - Convert lead to quote
- `POST /api/commerce/leads/{id}/forward_to_distributor/` - Forward to distributor
- `POST /api/commerce/leads/{id}/accept_by_distributor/` - Distributor accepts
- `POST /api/commerce/leads/{id}/reject_by_distributor/` - Distributor rejects

### Commerce - Quotes
- `GET/POST /api/commerce/quotes/` - List/create quotes
- `POST /api/commerce/quotes/{id}/buyer_requests/` - Buyer submits quote
- `POST /api/commerce/quotes/{id}/seller_responds/` - Seller responds with pricing
- `POST /api/commerce/quotes/{id}/seller_modifies/` - Seller modifies quote
- `POST /api/commerce/quotes/{id}/buyer_responds/` - Buyer requests modification
- `POST /api/commerce/quotes/{id}/buyer_accepts/` - Buyer accepts (creates order)
- `POST /api/commerce/quotes/{id}/cancel/` - Cancel quote
- `POST /api/commerce/quotes/{id}/seller_declines/` - Seller declines
- `GET/POST /api/commerce/quote-items/` - Manage quote line items

### Commerce - Orders
- `GET/POST /api/commerce/orders/` - List/create orders
- `POST /api/commerce/orders/{id}/accept/` - Seller accepts order
- `POST /api/commerce/orders/{id}/make_in_progress/` - Start processing
- `POST /api/commerce/orders/{id}/invoice/` - Generate invoice
- `POST /api/commerce/orders/{id}/ship_order/` - Ship order
- `POST /api/commerce/orders/{id}/receive_payment/` - Receive payment
- `POST /api/commerce/orders/{id}/complete/` - Complete order
- `POST /api/commerce/orders/{id}/cancel/` - Cancel order
- `GET/POST /api/commerce/order-items/` - Manage order line items

### Commerce - Shipping
- `GET/POST /api/commerce/shipments/` - Manage shipment advice
- `GET/POST /api/commerce/price-tiers/` - Manage price tiers

### Commerce - Reference Data
- `GET/POST /api/commerce/delivery-terms/` - Delivery terms
- `GET/POST /api/commerce/payment-terms/` - Payment terms
- `GET/POST /api/commerce/payment-modes/` - Payment modes

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=commerce --cov=products --cov=tenants
```

### Run Specific Test Class
```bash
pytest commerce/tests.py::TestLeadFlow -v
pytest commerce/tests.py::TestQuoteFlow -v
pytest commerce/tests.py::TestOrderFlow -v
pytest commerce/tests.py::TestEndToEndFlow -v
```

### Test Coverage
98% code coverage with 153 comprehensive tests:
- ✅ Shopping cart with 59 tests (cart creation, items, conversion to lead)
- ✅ Products & SKUs with 51 tests (100% coverage)
- ✅ Tenants & associations with 43 tests (100% coverage)
- ✅ Lead creation and distributor forwarding
- ✅ Quote negotiation flow (request → respond → accept)
- ✅ Price tier resolution
- ✅ Order fulfillment (accept → process → invoice → ship → complete)
- ✅ Complete end-to-end Cart → Lead → Quote → Order → Shipment workflow
- ✅ All FSM state transitions tested
- ✅ Buyer/seller negotiation workflows

## Example Workflow

### 1. Create Tenants
```bash
# Create seller
POST /api/tenants/tenants/
{
  "name": "Acme Chemicals",
  "type": "seller",
  "email": "sales@acme.com"
}

# Create buyer
POST /api/tenants/tenants/
{
  "name": "Buyer Corp",
  "type": "buyer",
  "email": "procurement@buyer.com"
}
```

### 2. Create Product and SKU
```bash
# Create product
POST /api/products/products/
{
  "seller": "<seller_id>",
  "name": "Chemical X",
  "brand_product_name": "Acme Chemical X",
  "status": "published"
}

# Create SKU
POST /api/products/products/<product_id>/create_sku/
{
  "number": "SKU-001",
  "packaging_type": "<packaging_type_id>",
  "packaging_unit": "<packaging_unit_id>",
  "package_volume": "100.00"
}
```

### 3. Create Price Tier
```bash
POST /api/commerce/price-tiers/
{
  "seller": "<seller_id>",
  "buyer": "<buyer_id>",
  "destination": "<warehouse_address_id>",
  "product_sku": "<sku_id>",
  "minimum_uom_quantity": "500.00",
  "price_per_uom": "45.00",
  "currency": "USD",
  "is_active": true
}
```

### 4. Create Lead
```bash
POST /api/commerce/leads/
{
  "seller": "<seller_id>",
  "buyer_first_name": "John",
  "buyer_last_name": "Doe",
  "buyer_email": "john@buyer.com",
  "buyer_company_name": "Buyer Corp"
}

# Create the lead
POST /api/commerce/leads/<lead_id>/create_lead/
```

### 5. Create Quote Request
```bash
POST /api/commerce/quotes/
{
  "buyer": "<buyer_id>",
  "seller": "<seller_id>",
  "warehouse": "<warehouse_id>",
  "delivery_term": "<delivery_term_id>",
  "payment_term": "<payment_term_id>",
  "payment_mode": "<payment_mode_id>",
  "currency": "USD"
}

# Add items
POST /api/commerce/quote-items/
{
  "quote_request": "<quote_id>",
  "product": "<product_id>",
  "sku": "<sku_id>",
  "no_of_units": "10.00",
  "total_quantity": "1000.00",
  "currency": "USD"
}

# Buyer requests quote
POST /api/commerce/quotes/<quote_id>/buyer_requests/
```

### 6. Seller Responds
```bash
POST /api/commerce/quotes/<quote_id>/seller_responds/
{
  "items": [
    {"id": "<item_id>", "price_per_unit": "50.00"}
  ],
  "shipping_cost": "100.00"
}
```

### 7. Buyer Accepts (Creates Order)
```bash
POST /api/commerce/quotes/<quote_id>/buyer_accepts/
# Automatically creates PurchaseOrder
```

### 8. Fulfill Order
```bash
# Accept order
POST /api/commerce/orders/<order_id>/accept/

# Process
POST /api/commerce/orders/<order_id>/make_in_progress/

# Invoice
POST /api/commerce/orders/<order_id>/invoice/

# Ship
POST /api/commerce/orders/<order_id>/ship_order/

# Create shipment advice
POST /api/commerce/shipments/
{
  "order": "<order_id>",
  "carrier": "FedEx",
  "carrier_number": "TRACK123456",
  "estimated_time_of_arrival": "2024-12-31T00:00:00Z"
}

# Receive payment
POST /api/commerce/orders/<order_id>/receive_payment/

# Complete
POST /api/commerce/orders/<order_id>/complete/
```

## State Machine Transitions

### Lead States
```
no_lead → [create] → new → [convert] → converted
                              ↓
                         [forward_to_distributor]
                              ↓
                         forwarded → [accept_by_distributor] → accepted_by_distributor
```

### Quote States
```
no_request → [create_quote] → new → [buyer_requests] → requested
                                                    ↓
                                            [seller_responds]
                                                    ↓
                                            responded → [buyer_accepts] → accepted
                                                    ↓
                                            [seller_modifies] → requested (re-negotiation)
```

### Order States
```
no_order → [create_order] → new → [accept] → accepted → [make_in_progress] → in_progress
                                                                                    ↓
                                                                            [invoice] → invoiced
                                                                                    ↓
                                                                            [ship_order] → shipped
                                                                                    ↓
                                                                            [receive_payment] → payment_received
                                                                                    ↓
                                                                            [complete] → completed
```

## Project Structure

```
quorion-b2b-api/
├── quorion_api/          # Main project settings
│   ├── settings.py      # Django settings
│   ├── urls.py          # Root URL configuration
│   └── wsgi.py
├── tenants/             # Tenant management app
│   ├── models.py        # Tenant, TenantAddress, TenantAssociation
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── products/            # Product management app
│   ├── models.py        # Product, ProductSKU, PackagingType, PackagingUnit, ListPrice
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── commerce/            # Commerce/transaction app
│   ├── models.py        # Lead, QuoteRequest, PurchaseOrder, PriceTier, ShipmentAdvice
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py         # Comprehensive test suite
├── requirements.txt
├── pytest.ini
└── README.md
```

## Key Features

### Price Negotiation
- Automatic price resolution from price tiers based on quantity
- Manual price overrides
- Buyer-specific pricing
- Destination-specific pricing
- Volume-based tiered pricing

### Distributor Support
- Forward leads to distributors
- Create distributor-specific SKUs
- Distributor pricing tiers
- Parent-child lead relationships

### State Machine Enforcement
- All state transitions are enforced
- Invalid transitions are prevented
- Automatic state updates

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to:
- Manage tenants, products, and SKUs
- View and manage quotes and orders
- Configure price tiers
- Monitor transaction status

## API Documentation

The API uses Django REST Framework. You can:
- Browse the API at `http://localhost:8000/api/`
- Use the browsable API interface
- Filter results using query parameters (e.g., `?seller=<id>&status=requested`)

## Development

### Running Tests
```bash
# All tests
pytest

# Specific test
pytest commerce/tests.py::TestEndToEndFlow::test_complete_flow -v

# With coverage
pytest --cov=. --cov-report=html
```

### Database
The project uses SQLite by default (for MVP). To use PostgreSQL:
1. Update `DATABASES` in `settings.py`
2. Install `psycopg2-binary` (already in requirements.txt)

## License

This is an MVP implementation for demonstration purposes.

## Notes

- All endpoints are tested and working
- State machines are fully functional
- Price negotiation logic is complete
- End-to-end flow from lead to shipping is verified
- The system supports multi-tenant architecture with distributors

