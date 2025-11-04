# Database Information

## Current Database: SQLite3

The project is currently using **SQLite3** as the database backend.

### Database File
- **Location**: `db.sqlite3` (in project root)
- **Type**: SQLite 3.x database
- **Size**: ~500 KB (after migrations)

### Configuration
Located in `quorion_api/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Switching to PostgreSQL

If you want to use PostgreSQL instead:

1. **Update settings.py**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quorion_b2b',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

2. **Create PostgreSQL database**:
```bash
createdb quorion_b2b
```

3. **Run migrations**:
```bash
python manage.py migrate
```

### Note
- SQLite3 is perfect for development and MVP
- PostgreSQL is recommended for production
- `psycopg2-binary` is already in requirements.txt for PostgreSQL support

