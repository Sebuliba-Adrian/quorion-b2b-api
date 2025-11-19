# Security Implementation - JWT + RBAC

## Current Status: ⚠️ SECURITY CRITICAL

### Security Implementation Completed:
✅ JWT authentication configuration added
✅ Custom RBAC permissions created (`tenants/permissions.py`)
✅ Authentication endpoints created (`/api/auth/`)
✅ Settings updated with JWT and IsAuthenticated default

### Required Next Steps:
1. Install JWT package: `pip install djangorestframework-simplejwt==5.4.0`
2. Run migrations (JWT creates token blacklist tables)
3. Apply permission classes to all viewsets
4. Run RBAC tests
5. Update frontend to use JWT tokens

---

## Authentication Endpoints

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "tenant": {
      "id": "uuid",
      "name": "Seller Co",
      "type": "seller"
    }
  }
}
```

### Register
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_id": "uuid"  // optional
}
```

### Get Current User
```http
GET /api/auth/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Verify Token
```http
POST /api/auth/token/verify/
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## RBAC Permissions (tenants/permissions.py)

### Authentication Permissions
- **IsAuthenticated** - User must be logged in
- **IsTenantUser** - User must be associated with a tenant

### Tenant Type Permissions
- **IsSeller** - User's tenant must be type='seller'
- **IsBuyer** - User's tenant must be type='buyer'
- **IsDistributor** - User's tenant must be type='distributor'
- **IsSellerOrDistributor** - User's tenant is seller OR distributor

### Object-Level Permissions
- **IsTenantOwner** - User's tenant owns the object
- **IsSellerOfProduct** - User's tenant is the product seller
- **IsBuyerOrSeller** - User is either buyer or seller of the object
- **CanAccessOrder** - User is buyer or seller of the order
- **CanAccessQuote** - User is buyer or seller of the quote
- **CanAccessLead** - User is the seller who received the lead
- **IsOwnerOrReadOnly** - Owner can edit, others can read
- **ReadOnly** - Authenticated users can only read

---

## Endpoint Permission Mapping

### Products Endpoints

| Endpoint | Method | Permission Classes |
|----------|--------|-------------------|
| `/api/products/` | GET | `IsAuthenticated` |
| `/api/products/` | POST | `IsSeller` |
| `/api/products/{id}/` | GET | `IsAuthenticated` |
| `/api/products/{id}/` | PUT/PATCH | `IsSellerOfProduct` |
| `/api/products/{id}/` | DELETE | `IsSellerOfProduct` |
| `/api/products/images/` | POST | `IsSellerOfProduct` |
| `/api/products/categories/` | GET | `IsAuthenticated` |
| `/api/products/reviews/` | GET | `IsAuthenticated` |
| `/api/products/reviews/` | POST | `IsBuyer` (verified purchase) |

### Commerce Endpoints

| Endpoint | Method | Permission Classes |
|----------|--------|-------------------|
| `/api/commerce/carts/` | GET | `IsBuyer`, `IsTenantOwner` |
| `/api/commerce/carts/` | POST | `IsBuyer` |
| `/api/commerce/leads/` | GET | `IsSeller`, `CanAccessLead` |
| `/api/commerce/leads/` | POST | `IsBuyer` |
| `/api/commerce/quotes/` | GET | `CanAccessQuote` |
| `/api/commerce/quotes/` | POST | `IsBuyer` or `IsSeller` |
| `/api/commerce/orders/` | GET | `CanAccessOrder` |
| `/api/commerce/orders/` | POST | `IsBuyer` |
| `/api/commerce/payments/` | GET | `IsBuyerOrSeller` |
| `/api/commerce/notifications/` | GET | `IsTenantOwner` |

### Tenant Endpoints

| Endpoint | Method | Permission Classes |
|----------|--------|-------------------|
| `/api/tenants/` | GET | `IsAuthenticated` |
| `/api/tenants/` | POST | `AllowAny` (registration) |
| `/api/tenants/{id}/` | GET | `IsAuthenticated` |
| `/api/tenants/{id}/` | PUT/PATCH | `IsTenantOwner` |

---

## Installation Steps

### 1. Install JWT Package
```bash
pip install djangorestframework-simplejwt==5.4.0
```

### 2. Run Migrations
```bash
python manage.py migrate
```

This creates the token blacklist tables for JWT token rotation.

### 3. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

### 4. Test Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token
curl http://localhost:8000/api/products/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## JWT Configuration (already added to settings.py)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

---

## Frontend Integration

### React/Next.js Example

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Login
async function login(username: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
}

// Authenticated request
async function authenticatedFetch(url: string, options = {}) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  // Handle 401 - refresh token
  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry request with new token
      return authenticatedFetch(url, options);
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }

  return response.json();
}

// Refresh token
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');

  const response = await fetch(`${API_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return true;
  }

  return false;
}

// Get products (authenticated)
async function getProducts() {
  return authenticatedFetch('/api/products/');
}

// Create product (seller only)
async function createProduct(productData) {
  return authenticatedFetch('/api/products/', {
    method: 'POST',
    body: JSON.stringify(productData)
  });
}
```

---

## Security Best Practices

### ✅ Implemented
- JWT authentication with token rotation
- Token blacklisting on refresh
- HTTPS-only cookies (configure in production)
- CORS configuration
- Password hashing (Django default)
- RBAC with tenant-based access control

### 🔧 Production Checklist
- [ ] Set `SECRET_KEY` from environment variable
- [ ] Configure `CORS_ALLOW_ALL_ORIGINS = False`
- [ ] Add specific `CORS_ALLOWED_ORIGINS`
- [ ] Enable HTTPS only
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Set `CSRF_COOKIE_SECURE = True`
- [ ] Configure rate limiting
- [ ] Add logging for auth failures
- [ ] Set up monitoring/alerts
- [ ] Regular security audits

---

## Testing RBAC

```python
# tests/test_auth_rbac.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_unauthenticated_request_denied():
    """Unauthenticated requests should be denied"""
    client = APIClient()
    response = client.get('/api/products/')
    assert response.status_code == 401

@pytest.mark.django_db
def test_authenticated_request_allowed(seller_user, seller_token):
    """Authenticated requests should be allowed"""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {seller_token}')
    response = client.get('/api/products/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_buyer_cannot_create_product(buyer_user, buyer_token):
    """Buyers should not be able to create products"""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {buyer_token}')
    response = client.post('/api/products/', {
        'name': 'Test Product',
        'description': 'Test'
    })
    assert response.status_code == 403

@pytest.mark.django_db
def test_seller_can_create_product(seller_user, seller_token):
    """Sellers should be able to create products"""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {seller_token}')
    response = client.post('/api/products/', {
        'name': 'Test Product',
        'seller': seller_user.tenant.id
    })
    assert response.status_code in [200, 201]
```

---

## Troubleshooting

### "Authentication credentials were not provided"
- Missing `Authorization` header
- Check header format: `Authorization: Bearer <token>`

### "Token is invalid or expired"
- Access token expired (1 hour default)
- Use refresh token to get new access token

### "User does not have required tenant type"
- User's tenant type doesn't match required permission
- Check `user.tenant.type` matches endpoint requirements

### "Cannot access this resource"
- Object-level permission denied
- User's tenant doesn't own the resource
- Check buyer/seller relationship

---

## Next Steps

1. **Install JWT**: `pip install djangorestframework-simplejwt==5.4.0`
2. **Run migrations**: `python manage.py migrate`
3. **Test authentication**: Use Postman or curl to test `/api/auth/login/`
4. **Update frontend**: Implement JWT token handling
5. **Add permission classes**: Apply to all viewsets (see implementation guide below)
6. **Run RBAC tests**: Create and run comprehensive permission tests
7. **Production hardening**: Follow production checklist above
