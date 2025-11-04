# Complete API Endpoints Reference

## Base URL
`http://localhost:8000/api/`

## Tenants API

### Tenants
- `GET /api/tenants/tenants/` - List all tenants
- `POST /api/tenants/tenants/` - Create tenant
- `GET /api/tenants/tenants/{id}/` - Get tenant details
- `PUT /api/tenants/tenants/{id}/` - Update tenant
- `PATCH /api/tenants/tenants/{id}/` - Partial update tenant
- `DELETE /api/tenants/tenants/{id}/` - Delete tenant
- `GET /api/tenants/tenants/{id}/addresses/` - Get tenant addresses
- `GET /api/tenants/tenants/{id}/distributors/` - Get distributors (seller only)

### Tenant Addresses
- `GET /api/tenants/addresses/` - List addresses
- `POST /api/tenants/addresses/` - Create address
- `GET /api/tenants/addresses/{id}/` - Get address
- `PUT/PATCH/DELETE /api/tenants/addresses/{id}/` - Update/delete address

### Tenant Associations
- `GET /api/tenants/associations/` - List associations
- `POST /api/tenants/associations/` - Create association
- `GET/PUT/PATCH/DELETE /api/tenants/associations/{id}/` - Manage association

## Products API

### Products
- `GET /api/products/products/` - List products
- `POST /api/products/products/` - Create product
- `GET/PUT/PATCH/DELETE /api/products/products/{id}/` - Manage product
- `POST /api/products/products/{id}/create_sku/` - Create SKU for product

### Product SKUs
- `GET /api/products/skus/` - List SKUs
- `POST /api/products/skus/` - Create SKU
- `GET/PUT/PATCH/DELETE /api/products/skus/{id}/` - Manage SKU
- `POST /api/products/skus/{id}/create_distributor_copy/` - Create distributor copy

### Packaging
- `GET/POST /api/products/packaging-types/` - Manage packaging types
- `GET/POST /api/products/packaging-units/` - Manage packaging units
- `GET/POST /api/products/list-prices/` - Manage list prices

## Commerce API - Leads

### Leads
- `GET /api/commerce/leads/` - List leads
- `POST /api/commerce/leads/` - Create lead
- `GET/PUT/PATCH/DELETE /api/commerce/leads/{id}/` - Manage lead
- `POST /api/commerce/leads/{id}/create_lead/` - Initialize lead (state: new)
- `POST /api/commerce/leads/{id}/convert/` - Convert to quote
- `POST /api/commerce/leads/{id}/forward_to_distributor/` - Forward to distributor
- `POST /api/commerce/leads/{id}/accept_by_distributor/` - Distributor accepts
- `POST /api/commerce/leads/{id}/reject_by_distributor/` - Distributor rejects

## Commerce API - Quotes

### Quote Requests
- `GET /api/commerce/quotes/` - List quotes
- `POST /api/commerce/quotes/` - Create quote
- `GET/PUT/PATCH/DELETE /api/commerce/quotes/{id}/` - Manage quote
- `POST /api/commerce/quotes/{id}/buyer_requests/` - Buyer submits quote
- `POST /api/commerce/quotes/{id}/seller_responds/` - Seller responds with pricing
- `POST /api/commerce/quotes/{id}/seller_modifies/` - Seller modifies (re-negotiate)
- `POST /api/commerce/quotes/{id}/buyer_responds/` - Buyer requests modification
- `POST /api/commerce/quotes/{id}/buyer_accepts/` - Buyer accepts (creates order)
- `POST /api/commerce/quotes/{id}/cancel/` - Cancel quote
- `POST /api/commerce/quotes/{id}/seller_declines/` - Seller declines

### Quote Items
- `GET /api/commerce/quote-items/` - List quote items
- `POST /api/commerce/quote-items/` - Add item to quote
- `GET/PUT/PATCH/DELETE /api/commerce/quote-items/{id}/` - Manage quote item

## Commerce API - Orders

### Purchase Orders
- `GET /api/commerce/orders/` - List orders
- `POST /api/commerce/orders/` - Create order
- `GET/PUT/PATCH/DELETE /api/commerce/orders/{id}/` - Manage order
- `POST /api/commerce/orders/{id}/accept/` - Seller accepts order
- `POST /api/commerce/orders/{id}/make_in_progress/` - Start processing
- `POST /api/commerce/orders/{id}/invoice/` - Generate invoice
- `POST /api/commerce/orders/{id}/ship_order/` - Ship order
- `POST /api/commerce/orders/{id}/receive_payment/` - Receive payment
- `POST /api/commerce/orders/{id}/complete/` - Complete order
- `POST /api/commerce/orders/{id}/cancel/` - Cancel order

### Order Items
- `GET /api/commerce/order-items/` - List order items
- `POST /api/commerce/order-items/` - Add item to order
- `GET/PUT/PATCH/DELETE /api/commerce/order-items/{id}/` - Manage order item

## Commerce API - Shipping

### Shipment Advice
- `GET /api/commerce/shipments/` - List shipments
- `POST /api/commerce/shipments/` - Create shipment advice
- `GET/PUT/PATCH/DELETE /api/commerce/shipments/{id}/` - Manage shipment

### Price Tiers
- `GET /api/commerce/price-tiers/` - List price tiers
- `POST /api/commerce/price-tiers/` - Create price tier
- `GET/PUT/PATCH/DELETE /api/commerce/price-tiers/{id}/` - Manage price tier

## Commerce API - Reference Data

### Delivery Terms
- `GET/POST /api/commerce/delivery-terms/` - Manage delivery terms
- `GET/PUT/PATCH/DELETE /api/commerce/delivery-terms/{id}/` - Manage delivery term

### Payment Terms
- `GET/POST /api/commerce/payment-terms/` - Manage payment terms
- `GET/PUT/PATCH/DELETE /api/commerce/payment-terms/{id}/` - Manage payment term

### Payment Modes
- `GET/POST /api/commerce/payment-modes/` - Manage payment modes
- `GET/PUT/PATCH/DELETE /api/commerce/payment-modes/{id}/` - Manage payment mode

## Filtering

All list endpoints support filtering via query parameters:
- `?seller=<id>` - Filter by seller
- `?buyer=<id>` - Filter by buyer
- `?status=<status>` - Filter by status
- `?is_active=true` - Filter active items

Example: `GET /api/commerce/quotes/?seller=<id>&status=requested`

## Pagination

All list endpoints are paginated (20 items per page):
- `?page=1` - Page number
- `?page_size=50` - Items per page (max 100)

