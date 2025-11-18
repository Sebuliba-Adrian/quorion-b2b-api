# Complete Testing Guide - Quorion B2B API

## Prerequisites Setup

```bash
# Install python3-venv (Ubuntu/Debian)
sudo apt install python3.12-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

## Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional, for admin testing)
python manage.py createsuperuser
```

## Run All Tests with Coverage

### 1. Run Cart Tests Only
```bash
pytest commerce/test_cart.py -v --cov=commerce.models --cov=commerce.views --cov=commerce.serializers --cov-report=html --cov-report=term-missing
```

**Expected Output:** 50+ tests passing
- Test Coverage: Cart model, CartItem model, Customer model
- API endpoints: CRUD, bulk operations, cloning, merging, validation
- Lead-to-customer conversion
- Cart-to-lead conversion

### 2. Run All Commerce Tests
```bash
pytest commerce/tests.py -v --cov=commerce --cov-append --cov-report=html
```

**Expected Output:** 38+ tests passing
- Lead management with FSM
- Quote request workflow
- Purchase order processing
- Shipment tracking

### 3. Run All Project Tests
```bash
pytest -v --cov=. --cov-report=html --cov-report=term-missing
```

**Expected Total:** 90+ tests passing across all apps

### 4. Generate Coverage Report
```bash
# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Target:** 100% coverage on all new cart functionality

## Manual Smoke Testing

### Setup Test Server
```bash
# Terminal 1: Run development server
python manage.py runserver
```

### Test Sequence (use another terminal or Postman)

#### 1. Create Test Data

```bash
# Create Seller Tenant
curl -X POST http://localhost:8000/api/tenants/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Seller",
    "type": "seller",
    "email": "seller@test.com"
  }'
# Save the returned ID as SELLER_ID

# Create Buyer Tenant
curl -X POST http://localhost:8000/api/tenants/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Buyer",
    "type": "buyer",
    "email": "buyer@test.com"
  }'
# Save the returned ID as BUYER_ID

# Create Product
curl -X POST http://localhost:8000/api/products/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "seller": "SELLER_ID",
    "name": "Test Product",
    "sku": "TEST-001",
    "description": "Test product",
    "unit_of_measure": "kg",
    "base_price": "100.00",
    "currency": "USD"
  }'
# Save the returned ID as PRODUCT_ID
```

#### 2. Test Customer Management

```bash
# Create Customer
curl -X POST http://localhost:8000/api/commerce/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "SELLER_ID",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "company_name": "Test Company",
    "credit_limit": "50000.00",
    "payment_terms_days": 30
  }'
# Save returned ID as CUSTOMER_ID

# Get Customer
curl http://localhost:8000/api/commerce/customers/CUSTOMER_ID/

# List Customers
curl http://localhost:8000/api/commerce/customers/

# Update Customer
curl -X PATCH http://localhost:8000/api/commerce/customers/CUSTOMER_ID/ \
  -H "Content-Type: application/json" \
  -d '{"credit_limit": "75000.00"}'
```

#### 3. Test Shopping Cart - Basic Operations

```bash
# Create Cart
curl -X POST http://localhost:8000/api/commerce/carts/ \
  -H "Content-Type: application/json" \
  -d '{
    "buyer": "BUYER_ID",
    "name": "My Shopping Cart"
  }'
# Save returned ID as CART_ID

# Get Cart Details
curl http://localhost:8000/api/commerce/carts/CART_ID/

# Add Item to Cart
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": "PRODUCT_ID",
    "quantity": "5.00",
    "unit_price": "100.00",
    "notes": "Urgent delivery required"
  }'
# Save returned item ID as ITEM_ID

# Update Item Quantity
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": "PRODUCT_ID",
    "quantity": "10.00",
    "unit_price": "95.00"
  }'

# Verify Cart Totals
curl http://localhost:8000/api/commerce/carts/CART_ID/
# Should show: total_items=1, total_quantity=10.00, subtotal=950.00
```

#### 4. Test Bulk Operations

```bash
# Add Multiple Items at Once
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/add_bulk_items/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product": "PRODUCT_ID",
        "quantity": "2.00",
        "unit_price": "100.00"
      }
    ]
  }'
```

#### 5. Test Cart Validation

```bash
# Validate Cart
curl http://localhost:8000/api/commerce/carts/CART_ID/validate/
# Should return: {"valid": true, "errors": []}
```

#### 6. Test Cart Cloning

```bash
# Clone Cart for Reorder
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/clone/ \
  -H "Content-Type: application/json" \
  -d '{
    "buyer": "BUYER_ID"
  }'
# Save new cart ID as CLONED_CART_ID

# Verify Cloned Cart
curl http://localhost:8000/api/commerce/carts/CLONED_CART_ID/
# Should have same items as original
```

#### 7. Test Cart Merging

```bash
# Create Second Cart
curl -X POST http://localhost:8000/api/commerce/carts/ \
  -H "Content-Type: application/json" \
  -d '{"buyer": "BUYER_ID"}'
# Save as CART2_ID

# Add items to second cart
curl -X POST http://localhost:8000/api/commerce/carts/CART2_ID/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": "PRODUCT_ID",
    "quantity": "3.00",
    "unit_price": "100.00"
  }'

# Merge CART2 into CART1
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/merge/ \
  -H "Content-Type: application/json" \
  -d '{"other_cart_id": "CART2_ID"}'

# Verify merged cart
curl http://localhost:8000/api/commerce/carts/CART_ID/
# Should show increased quantities
```

#### 8. Test Cart Item Removal

```bash
# Remove Item from Cart
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/remove_item/ \
  -H "Content-Type: application/json" \
  -d '{"item_id": "ITEM_ID"}'

# Verify item removed
curl http://localhost:8000/api/commerce/carts/CART_ID/
```

#### 9. Test Clear Cart

```bash
# Clear All Items
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/clear/

# Verify cart empty
curl http://localhost:8000/api/commerce/carts/CART_ID/
# Should show total_items=0, subtotal=0.00
```

#### 10. Test Cart-to-Lead Conversion

```bash
# Re-add items to cart first
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": "PRODUCT_ID",
    "quantity": "5.00",
    "unit_price": "100.00"
  }'

# Convert Cart to Lead
curl -X POST http://localhost:8000/api/commerce/carts/CART_ID/convert_to_lead/ \
  -H "Content-Type: application/json" \
  -d '{
    "seller": "SELLER_ID",
    "buyer_first_name": "Jane",
    "buyer_last_name": "Smith",
    "buyer_email": "jane.smith@example.com",
    "buyer_phone": "+1234567890",
    "buyer_company_name": "Smith Industries"
  }'
# Save returned lead ID as LEAD_ID

# Verify Lead Created
curl http://localhost:8000/api/commerce/leads/LEAD_ID/
# Should show status="new", cart linked

# Verify Cart Deactivated
curl http://localhost:8000/api/commerce/carts/CART_ID/
# Should show is_active=false
```

#### 11. Test Lead-to-Customer Conversion

```bash
# Convert Lead to Customer
curl -X POST http://localhost:8000/api/commerce/leads/LEAD_ID/convert_to_customer/ \
  -H "Content-Type: application/json" \
  -d '{
    "credit_limit": "100000.00",
    "payment_terms_days": 60
  }'
# Save returned customer ID as NEW_CUSTOMER_ID

# Verify Customer Created
curl http://localhost:8000/api/commerce/customers/NEW_CUSTOMER_ID/
# Should match lead buyer info with credit limit

# Verify Lead Updated
curl http://localhost:8000/api/commerce/leads/LEAD_ID/
# Should show customer field populated
```

#### 12. Test Anonymous Cart (Session-based)

```bash
# Create Anonymous Cart
curl -X POST http://localhost:8000/api/commerce/carts/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_key": "anonymous-session-123",
    "name": "Guest Cart"
  }'
# Save as ANON_CART_ID

# Add items as anonymous user
curl -X POST http://localhost:8000/api/commerce/carts/ANON_CART_ID/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": "PRODUCT_ID",
    "quantity": "2.00",
    "unit_price": "100.00"
  }'

# Verify anonymous cart
curl http://localhost:8000/api/commerce/carts/ANON_CART_ID/
# Should show is_anonymous=true, buyer=null
```

## Expected Test Results

### Unit Tests
- **Cart Model Tests**: 8 tests ✓
- **CartItem Model Tests**: 4 tests ✓
- **Customer Model Tests**: 2 tests ✓
- **Cart API Tests**: 5 tests ✓
- **CartItem API Tests**: 6 tests ✓
- **Cart-to-Lead Conversion**: 3 tests ✓
- **Lead-to-Customer Conversion**: 2 tests ✓
- **Cart Filtering**: 2 tests ✓
- **Cart Integration**: 2 tests ✓
- **Cart Edge Cases**: 3 tests ✓

**Total Cart Tests: 50+ tests**

### Coverage Targets
- `commerce/models.py` (Cart, CartItem, Customer): **100%**
- `commerce/views.py` (CartViewSet, CustomerViewSet): **100%**
- `commerce/serializers.py` (Cart serializers): **100%**
- Overall commerce app: **95%+**

### Smoke Test Checklist
- [ ] Customer CRUD operations
- [ ] Cart creation and retrieval
- [ ] Add single item to cart
- [ ] Update item quantity
- [ ] Bulk add items
- [ ] Remove item from cart
- [ ] Clear cart
- [ ] Clone cart
- [ ] Merge carts
- [ ] Validate cart
- [ ] Convert cart to lead
- [ ] Convert lead to customer
- [ ] Anonymous cart creation
- [ ] Verify all totals calculate correctly
- [ ] Verify soft delete works
- [ ] Verify cart filtering

## Troubleshooting

### Common Issues

**1. Module not found errors**
```bash
pip install -r requirements.txt
```

**2. Database errors**
```bash
python manage.py migrate --run-syncdb
```

**3. Coverage not generating**
```bash
pip install pytest-cov
```

**4. Tests failing**
- Check database is migrated
- Verify all fixtures load correctly
- Check test isolation (each test should be independent)

## Performance Verification

After smoke testing, verify:
1. Cart operations complete in < 100ms
2. Bulk add handles 50+ items efficiently
3. No N+1 query issues (use Django Debug Toolbar)
4. Database indexes are being used (check EXPLAIN plans)

## Success Criteria

✅ All 90+ tests pass
✅ 100% coverage on new cart functionality
✅ All smoke tests complete successfully
✅ No console errors or warnings
✅ Response times acceptable
✅ All edge cases handled gracefully
