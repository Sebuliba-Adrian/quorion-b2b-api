# Marketplace Features Documentation

## Overview

The quorion-b2b-api now supports a complete **marketplace mode** in addition to the traditional B2B negotiation workflow. This allows the platform to function as a full-featured e-commerce marketplace with direct checkout, reviews, ratings, wishlists, and more.

## Table of Contents

1. [Architecture](#architecture)
2. [Features](#features)
3. [API Endpoints](#api-endpoints)
4. [Models](#models)
5. [Workflows](#workflows)
6. [Testing](#testing)
7. [Frontend Integration](#frontend-integration)

---

## Architecture

### Dual-Mode System

The platform supports two distinct workflows:

**B2B Mode (Traditional):**
```
Cart → Lead → Quote → Negotiation → Purchase Order → Shipment → Delivery
```

**Marketplace Mode (Direct):**
```
Cart → Direct Checkout → Payment → Purchase Order → Shipment → Delivery
```

Both modes coexist and can be enabled/disabled via the `MarketplaceConfig` model.

### Key Design Principles

- **Separation of Concerns**: Marketplace features are in separate `marketplace_models.py` files
- **Backwards Compatible**: All existing B2B functionality remains intact
- **Feature Flags**: Marketplace features can be toggled on/off per seller
- **API-First**: All features exposed through RESTful APIs
- **Test Coverage**: 92% overall, 95-100% for marketplace models

---

## Features

### 1. Product Categories & Hierarchy

**Location**: `products/marketplace_models.py:13-76`

Hierarchical category system with unlimited depth:

```python
category = ProductCategory.objects.create(
    name="Electronics",
    slug="electronics",
    parent=None  # Root category
)

subcategory = ProductCategory.objects.create(
    name="Smartphones",
    slug="smartphones",
    parent=category
)
```

**Features**:
- SEO-friendly slugs
- Breadcrumb navigation
- Ancestor/descendant queries
- Category images and icons
- Display ordering

**API Methods**:
- `GET /api/products/categories/` - List all categories
- `GET /api/products/categories/{slug}/` - Get category details
- `GET /api/products/categories/root_categories/` - Get root categories
- `GET /api/products/categories/{slug}/children/` - Get child categories
- `GET /api/products/categories/{slug}/products/` - Get products in category

### 2. Product Images & Media

**Location**: `products/marketplace_models.py:78-104`

Multiple images per product with automatic primary image management:

```python
image = ProductImage.objects.create(
    product=product,
    image_url="https://cdn.example.com/product.jpg",
    alt_text="Product main view",
    is_primary=True,
    order=1
)
```

**Features**:
- CDN/S3 URL support
- Primary image auto-designation
- Image ordering
- Alt text for accessibility

### 3. Product Variants & Attributes

**Location**: `products/marketplace_models.py:106-180`

Flexible attribute system for product variations:

```python
# Define attributes
color_attr = ProductAttribute.objects.create(name="Color", slug="color")
red_value = ProductAttributeValue.objects.create(
    attribute=color_attr,
    value="Red",
    slug="red"
)

# Create variant
variant = ProductVariant.objects.create(
    product=product,
    sku=product_sku,
    name="Red - Large",
    price_adjustment=Decimal("5.00"),  # +$5 for this variant
    stock_quantity=100
)
```

**Features**:
- Unlimited attributes per product
- Price adjustments per variant
- Stock tracking per variant
- Variant-specific inventory

### 4. Product Reviews & Ratings

**Location**: `products/marketplace_models.py:182-244`

Comprehensive review system with verification:

```python
review = ProductReview.objects.create(
    product=product,
    buyer=buyer_tenant,
    rating=5,
    title="Excellent product!",
    review="This product exceeded my expectations...",
    is_verified_purchase=True,  # Set if review is from actual purchase
    is_approved=False  # Requires moderation
)
```

**Features**:
- 1-5 star ratings
- Verified purchase badges
- Review approval workflow
- Helpful count tracking
- Title and detailed review text

**Seller Ratings**:
```python
rating = SellerRating.objects.create(
    seller=seller_tenant,
    buyer=buyer_tenant,
    rating=4,
    communication_rating=5,
    shipping_speed_rating=4,
    product_quality_rating=4,
    review="Great seller, fast shipping!"
)
```

Multi-dimensional seller ratings:
- Overall rating
- Communication
- Shipping speed
- Product quality

### 5. Wishlist System

**Location**: `products/marketplace_models.py:246-292`

Public and private wishlists:

```python
wishlist = Wishlist.objects.create(
    buyer=buyer_tenant,
    name="Holiday Shopping",
    is_public=False,
    is_active=True
)

item = WishlistItem.objects.create(
    wishlist=wishlist,
    product=product,
    variant=variant,
    notes="For birthday gift"
)
```

**API Methods**:
- `POST /api/products/wishlists/{id}/add_item/` - Add item
- `POST /api/products/wishlists/{id}/remove_item/` - Remove item
- `POST /api/products/wishlists/{id}/clear/` - Clear all items

### 6. Inventory Management

**Location**: `products/marketplace_models.py:311-344`

Multi-warehouse inventory tracking:

```python
inventory = Inventory.objects.create(
    product=product,
    sku=sku,
    warehouse=warehouse,
    quantity_available=100,
    quantity_reserved=10,
    quantity_incoming=50,
    reorder_level=20
)

# Check if reorder needed
if inventory.needs_reorder:
    # Trigger reorder workflow
    pass
```

**Features**:
- Multi-warehouse support
- Available/reserved/incoming quantities
- Reorder level alerts
- Last restocked timestamp

**API Methods**:
- `POST /api/products/inventory/{id}/adjust_quantity/` - Adjust inventory
- `GET /api/products/inventory/low_stock/` - Get low stock items

### 7. Notification System

**Location**: `commerce/marketplace_models.py:16-59`

Flexible notification system:

```python
notification = Notification.objects.create(
    recipient=buyer_tenant,
    notification_type="order_update",
    title="Order Shipped",
    message="Your order #12345 has been shipped",
    action_url="/orders/12345"
)
```

**Notification Types**:
- `order_update` - Order status changes
- `payment_update` - Payment confirmations
- `shipping_update` - Shipping updates
- `promotion` - Marketing promotions
- `price_drop` - Price drop alerts
- `back_in_stock` - Inventory alerts
- `review_reminder` - Review reminders
- `general` - General messages

**API Methods**:
- `POST /api/commerce/notifications/{id}/mark_read/` - Mark as read
- `POST /api/commerce/notifications/mark_all_read/` - Mark all read
- `GET /api/commerce/notifications/unread_count/` - Get unread count

### 8. Payment Processing

**Location**: `commerce/marketplace_models.py:84-111`

Stripe-ready payment models:

```python
payment = Payment.objects.create(
    order=order,
    payment_method="credit_card",
    amount=Decimal("129.99"),
    currency="USD",
    status="pending"
)

# Process payment (integrate with Stripe)
payment.status = "completed"
payment.paid_at = timezone.now()
payment.gateway_payment_id = "pi_xyz123"
payment.save()
```

**Payment Methods**:
- Credit Card
- Debit Card
- Bank Transfer
- PayPal
- Apple Pay
- Google Pay
- Cryptocurrency

**Payment Statuses**:
- Pending
- Processing
- Completed
- Failed
- Refunded
- Cancelled

**API Methods**:
- `POST /api/commerce/payments/{id}/process/` - Process payment
- `POST /api/commerce/payments/{id}/refund/` - Refund payment

### 9. Direct Checkout Flow

**Location**: `commerce/marketplace_models.py:113-161`

Streamlined checkout bypassing quote negotiation:

```python
checkout = DirectCheckout.objects.create(
    cart=cart,
    buyer=buyer_tenant,
    shipping_address=shipping_address,
    billing_address=billing_address,
    payment_method="credit_card",
    delivery_term=delivery_term,
    payment_term=payment_term,
    subtotal=Decimal("100.00"),
    tax_amount=Decimal("8.00"),
    shipping_cost=Decimal("10.00"),
    discount_amount=Decimal("5.00")
)

# Calculate totals
checkout.calculate_totals()  # Updates total_amount

# Complete checkout
checkout.is_completed = True
checkout.order = created_order
checkout.save()
```

**API Methods**:
- `POST /api/commerce/checkout/{id}/calculate/` - Calculate totals
- `POST /api/commerce/checkout/{id}/apply_promo_code/` - Apply promo code
- `POST /api/commerce/checkout/{id}/complete/` - Complete checkout

### 10. Promo Code System

**Location**: `commerce/marketplace_models.py:214-279`

Flexible discount system:

```python
# Percentage discount
promo = PromoCode.objects.create(
    code="SAVE10",
    discount_type="percentage",
    discount_value=Decimal("10.00"),
    min_purchase_amount=Decimal("50.00"),
    max_discount_amount=Decimal("20.00"),
    usage_limit=100,
    per_user_limit=1,
    valid_from=timezone.now(),
    valid_until=timezone.now() + timedelta(days=30)
)

# Check validity
if promo.is_valid():
    discount = promo.calculate_discount(cart_total)
```

**Features**:
- Percentage and fixed amount discounts
- Minimum purchase requirements
- Maximum discount caps
- Total usage limits
- Per-user limits
- Date range validity
- Product/category restrictions

**API Methods**:
- `POST /api/commerce/promo-codes/{code}/validate/` - Validate promo code

### 11. Analytics & Tracking

**Product Views** (`commerce/marketplace_models.py:163-188`):
```python
ProductView.objects.create(
    product=product,
    viewer=buyer_tenant,  # Can be null for anonymous
    ip_address=request.META['REMOTE_ADDR'],
    user_agent=request.META['HTTP_USER_AGENT']
)
```

**Search Analytics** (`commerce/marketplace_models.py:190-212`):
```python
SearchQuery.objects.create(
    query="laptop",
    searcher=buyer_tenant,  # Can be null for anonymous
    results_count=25,
    filters={"category": "electronics", "price_max": 1000}
)
```

**API Methods**:
- `GET /api/commerce/product-views/analytics/` - View analytics
- `GET /api/commerce/search-queries/popular_searches/` - Popular searches
- `GET /api/commerce/search-queries/trending/` - Trending searches

### 12. Advanced Search & Filtering

**Location**: `products/filters.py`

Comprehensive product filtering:

```python
# Filter products
products = Product.objects.all()
filterset = ProductFilter(request.GET, queryset=products)
filtered_products = filterset.qs
```

**Available Filters**:
- **Text Search**: Searches name, description, brand
- **Category**: Includes all descendants
- **Price Range**: Min/max price
- **Seller**: By seller ID or name
- **Tags**: Multiple tag filtering
- **Rating**: Minimum average rating
- **Stock**: In stock / out of stock
- **Featured**: Featured products only
- **Status**: Draft / Published / Archived

**Query Examples**:
```
GET /api/products/products/?search=laptop&min_price=500&max_price=1500&category_slug=electronics&min_rating=4&in_stock=true&ordering=-view_count
```

---

## API Endpoints

### Products

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products/products/` | GET | List products (with filtering) |
| `/api/products/products/{id}/` | GET | Get product details |
| `/api/products/categories/` | GET | List categories |
| `/api/products/categories/{slug}/` | GET | Get category |
| `/api/products/categories/root_categories/` | GET | Get root categories |
| `/api/products/categories/{slug}/children/` | GET | Get child categories |
| `/api/products/categories/{slug}/products/` | GET | Get category products |
| `/api/products/images/` | GET, POST | Manage images |
| `/api/products/images/{id}/set_primary/` | POST | Set primary image |
| `/api/products/attributes/` | GET, POST | Manage attributes |
| `/api/products/attribute-values/` | GET, POST | Manage attribute values |
| `/api/products/variants/` | GET, POST | Manage variants |
| `/api/products/reviews/` | GET, POST | Manage reviews |
| `/api/products/reviews/{id}/approve/` | POST | Approve review |
| `/api/products/reviews/{id}/mark_helpful/` | POST | Mark helpful |
| `/api/products/reviews/by_product/` | GET | Get product reviews |
| `/api/products/seller-ratings/` | GET, POST | Manage seller ratings |
| `/api/products/seller-ratings/{id}/approve/` | POST | Approve rating |
| `/api/products/seller-ratings/by_seller/` | GET | Get seller stats |
| `/api/products/wishlists/` | GET, POST | Manage wishlists |
| `/api/products/wishlists/{id}/add_item/` | POST | Add wishlist item |
| `/api/products/wishlists/{id}/remove_item/` | POST | Remove item |
| `/api/products/wishlists/{id}/clear/` | POST | Clear wishlist |
| `/api/products/tags/` | GET, POST | Manage tags |
| `/api/products/inventory/` | GET, POST | Manage inventory |
| `/api/products/inventory/{id}/adjust_quantity/` | POST | Adjust quantity |
| `/api/products/inventory/low_stock/` | GET | Low stock items |

### Commerce

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/commerce/notifications/` | GET | List notifications |
| `/api/commerce/notifications/{id}/mark_read/` | POST | Mark as read |
| `/api/commerce/notifications/mark_all_read/` | POST | Mark all read |
| `/api/commerce/notifications/unread_count/` | GET | Unread count |
| `/api/commerce/payments/` | GET, POST | Manage payments |
| `/api/commerce/payments/{id}/process/` | POST | Process payment |
| `/api/commerce/payments/{id}/refund/` | POST | Refund payment |
| `/api/commerce/checkout/` | GET, POST | Manage checkouts |
| `/api/commerce/checkout/{id}/calculate/` | POST | Calculate totals |
| `/api/commerce/checkout/{id}/apply_promo_code/` | POST | Apply promo code |
| `/api/commerce/checkout/{id}/complete/` | POST | Complete checkout |
| `/api/commerce/product-views/` | GET, POST | Track views |
| `/api/commerce/product-views/analytics/` | GET | View analytics |
| `/api/commerce/search-queries/` | GET, POST | Track searches |
| `/api/commerce/search-queries/popular_searches/` | GET | Popular searches |
| `/api/commerce/search-queries/trending/` | GET | Trending searches |
| `/api/commerce/promo-codes/` | GET, POST | Manage promo codes |
| `/api/commerce/promo-codes/{code}/validate/` | POST | Validate code |

---

## Models

### Product Models

| Model | Fields | Purpose |
|-------|--------|---------|
| `ProductCategory` | name, slug, parent, description, image, icon | Hierarchical categories |
| `ProductImage` | product, image_url, alt_text, is_primary, order | Product images |
| `ProductAttribute` | name, slug, description | Attribute definitions (Color, Size) |
| `ProductAttributeValue` | attribute, value, slug | Attribute values (Red, Large) |
| `ProductVariant` | product, sku, name, price_adjustment, stock_quantity | Product variations |
| `ProductReview` | product, buyer, rating, title, review, is_verified_purchase | Customer reviews |
| `SellerRating` | seller, buyer, rating, communication_rating, shipping_speed_rating | Seller ratings |
| `Wishlist` | buyer, name, is_public, is_active | Wishlists |
| `WishlistItem` | wishlist, product, variant, notes | Wishlist items |
| `ProductTag` | name, slug | Product tags |
| `Inventory` | product, sku, warehouse, quantity_available, quantity_reserved, reorder_level | Inventory tracking |

### Commerce Models

| Model | Fields | Purpose |
|-------|--------|---------|
| `Notification` | recipient, notification_type, title, message, is_read | User notifications |
| `Payment` | order, payment_method, amount, status, gateway_payment_id | Payment processing |
| `DirectCheckout` | cart, buyer, shipping_address, payment_method, subtotal, total_amount | Direct checkout |
| `ProductView` | product, viewer, ip_address, user_agent, viewed_at | View analytics |
| `SearchQuery` | query, searcher, results_count, filters | Search analytics |
| `PromoCode` | code, discount_type, discount_value, usage_limit, valid_from, valid_until | Discount codes |

---

## Workflows

### Direct Checkout Workflow

```python
# 1. Customer adds items to cart
cart = Cart.objects.create(buyer=buyer_tenant)
CartItem.objects.create(
    cart=cart,
    product=product,
    quantity=2,
    unit_price=product.base_price
)

# 2. Create checkout session
checkout = DirectCheckout.objects.create(
    cart=cart,
    buyer=buyer_tenant,
    shipping_address=shipping_address,
    billing_address=billing_address,
    payment_method="credit_card",
    delivery_term=delivery_term,
    payment_term=payment_term
)

# 3. Apply promo code (optional)
promo = PromoCode.objects.get(code="SAVE10")
if promo.is_valid():
    checkout.discount_amount = promo.calculate_discount(checkout.subtotal)
    promo.usage_count += 1
    promo.save()

# 4. Calculate totals
checkout.calculate_totals()

# 5. Process payment
payment = Payment.objects.create(
    order=checkout.order,
    payment_method=checkout.payment_method,
    amount=checkout.total_amount,
    status="processing"
)

# Integrate with Stripe/PayPal here
payment.status = "completed"
payment.paid_at = timezone.now()
payment.save()

# 6. Complete checkout
checkout.is_completed = True
checkout.completed_at = timezone.now()
checkout.save()

# 7. Clear cart
cart.is_active = False
cart.save()

# 8. Send notification
Notification.objects.create(
    recipient=buyer_tenant,
    notification_type="order_update",
    title="Order Confirmed",
    message=f"Your order has been confirmed. Total: ${checkout.total_amount}"
)
```

### B2B Negotiation Workflow (Existing)

```python
# 1. Cart → Lead
lead = Lead.objects.create_from_cart(
    cart=cart,
    buyer_email=buyer_email,
    buyer_company_name=company_name
)

# 2. Lead → Quote
quote = QuoteRequest.objects.create(
    buyer=buyer_tenant,
    seller=seller_tenant,
    status="pending"
)

# 3. Negotiation
quote.status = "seller_responded"
quote.save()

# 4. Quote → Order
order = PurchaseOrder.objects.create(
    buyer=buyer_tenant,
    seller=seller_tenant,
    status="confirmed"
)
```

---

## Testing

### Test Coverage

```
Overall Coverage: 92%
- Products Models: 95-100%
- Commerce Models: 95-100%
- Serializers: 90-100%
- Views: 34-97% (lower for API views)
```

### Running Tests

```bash
# Run all tests
pytest

# Run marketplace tests only
pytest products/test_marketplace_models.py commerce/test_marketplace_models.py

# Run with coverage
pytest --cov=products --cov=commerce --cov-report=term-missing

# Run specific test
pytest products/test_marketplace_models.py::TestProductCategory::test_category_creation
```

### Test Statistics

- **Total Tests**: 238
- **Marketplace Tests**: 39
- **B2B Tests**: 199
- **Pass Rate**: 100%

---

## Frontend Integration

### Next.js/React Example

```typescript
// Product Listing with Filtering
const ProductListing = () => {
  const [products, setProducts] = useState([])
  const [filters, setFilters] = useState({
    search: '',
    category: '',
    min_price: '',
    max_price: '',
    min_rating: '',
    in_stock: true
  })

  useEffect(() => {
    const params = new URLSearchParams(filters)
    fetch(`/api/products/products/?${params}`)
      .then(res => res.json())
      .then(data => setProducts(data.results))
  }, [filters])

  return (
    <div>
      <SearchBar onChange={(value) => setFilters({...filters, search: value})} />
      <CategoryFilter onChange={(value) => setFilters({...filters, category: value})} />
      <PriceRange
        onMinChange={(value) => setFilters({...filters, min_price: value})}
        onMaxChange={(value) => setFilters({...filters, max_price: value})}
      />
      <ProductGrid products={products} />
    </div>
  )
}

// Direct Checkout Flow
const Checkout = ({ cartId }) => {
  const processCheckout = async () => {
    // 1. Create checkout
    const checkout = await fetch('/api/commerce/checkout/', {
      method: 'POST',
      body: JSON.stringify({
        cart: cartId,
        shipping_address: shippingAddressId,
        payment_method: 'credit_card'
      })
    }).then(res => res.json())

    // 2. Apply promo code
    if (promoCode) {
      await fetch(`/api/commerce/checkout/${checkout.id}/apply_promo_code/`, {
        method: 'POST',
        body: JSON.stringify({ promo_code: promoCode })
      })
    }

    // 3. Calculate totals
    const updated = await fetch(`/api/commerce/checkout/${checkout.id}/calculate/`, {
      method: 'POST'
    }).then(res => res.json())

    // 4. Process payment with Stripe
    const stripe = await loadStripe(publicKey)
    const { error, paymentIntent } = await stripe.confirmCardPayment(
      clientSecret,
      { payment_method: paymentMethodId }
    )

    if (!error) {
      // 5. Complete checkout
      await fetch(`/api/commerce/checkout/${checkout.id}/complete/`, {
        method: 'POST'
      })
    }
  }
}

// Product Reviews
const ProductReviews = ({ productId }) => {
  const [reviews, setReviews] = useState([])

  useEffect(() => {
    fetch(`/api/products/reviews/by_product/?product_id=${productId}`)
      .then(res => res.json())
      .then(data => setReviews(data))
  }, [productId])

  const submitReview = async (reviewData) => {
    await fetch('/api/products/reviews/', {
      method: 'POST',
      body: JSON.stringify({
        product: productId,
        rating: reviewData.rating,
        title: reviewData.title,
        review: reviewData.text
      })
    })
  }

  return (
    <div>
      <ReviewForm onSubmit={submitReview} />
      <ReviewList reviews={reviews} />
    </div>
  )
}

// Wishlist Management
const Wishlist = ({ wishlistId }) => {
  const addToWishlist = async (productId, variantId = null) => {
    await fetch(`/api/products/wishlists/${wishlistId}/add_item/`, {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        variant_id: variantId,
        notes: 'Want this for birthday'
      })
    })
  }

  const removeFromWishlist = async (itemId) => {
    await fetch(`/api/products/wishlists/${wishlistId}/remove_item/`, {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId })
    })
  }
}
```

---

## Performance Considerations

1. **Database Indexes**: All foreign keys and frequently queried fields are indexed
2. **Query Optimization**: Use `select_related()` and `prefetch_related()` for related data
3. **Caching**: Consider Redis caching for product lists, categories, and analytics
4. **CDN**: Use CDN for product images to reduce server load
5. **Pagination**: All list endpoints support pagination (default 20 items per page)

---

## Security Considerations

1. **Review Moderation**: All reviews require approval before display
2. **Payment Security**: Never store credit card data, use Stripe/PayPal
3. **Rate Limiting**: Implement rate limiting on API endpoints
4. **Input Validation**: All user inputs are validated and sanitized
5. **SQL Injection**: Django ORM prevents SQL injection attacks
6. **XSS Protection**: All user-generated content is escaped

---

## Future Enhancements

Potential features to add:

1. **Product Recommendations**: Collaborative filtering or AI-based recommendations
2. **Live Chat**: Real-time customer support
3. **Product Comparisons**: Side-by-side product comparison
4. **Advanced Analytics**: Sales reports, conversion tracking, A/B testing
5. **Multi-Currency**: Support for multiple currencies
6. **Multi-Language**: Internationalization support
7. **Social Sharing**: Share products on social media
8. **Email Marketing**: Abandoned cart emails, promotional campaigns
9. **Loyalty Program**: Points, rewards, referral bonuses
10. **Subscription Products**: Recurring orders and subscriptions

---

## Support

For questions or issues:
- Check the API documentation: `/api/docs/`
- Review test files for usage examples
- Submit issues on GitHub

---

## License

Copyright © 2025 Quorion B2B Platform. All rights reserved.
