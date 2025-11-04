# Quick Start Guide - Quorion B2B API

## Current Database
**SQLite3** - See `DATABASE_INFO.md` for details

## Quick Commands

### Activate Virtual Environment
```bash
cd /home/adrian/Desktop/Projects/quorion-b2b-api
source venv/bin/activate
```

### Run Server
```bash
python manage.py runserver
```

### Run Tests
```bash
pytest commerce/tests.py -v
# or
./venv/bin/pytest commerce/tests.py -v
```

### Run Migrations
```bash
python manage.py migrate
```

### Access API
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## Project Structure
- **Main Project**: `quorion_api/`
- **Apps**: `tenants/`, `products/`, `commerce/`
- **Database**: SQLite3 (`db.sqlite3`)

## All Tests Passing ✅
- 13/13 tests passing
- 94% code coverage
- End-to-end flow verified

