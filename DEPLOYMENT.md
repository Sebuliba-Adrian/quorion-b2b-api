# Deployment Guide

## Repository Information

**GitHub Repository**: https://github.com/Sebuliba-Adrian/quorion-b2b-api

## CI/CD Status

The repository includes comprehensive CI/CD workflows:

1. **CI/CD Pipeline** (`.github/workflows/ci.yml`)
   - Runs tests on Python 3.11 and 3.12
   - Tests with PostgreSQL database
   - Generates coverage reports
   - Uploads to Codecov
   - Runs linting (flake8, black, isort)
   - Code quality checks (pylint)

2. **CodeQL Analysis** (`.github/workflows/codeql.yml`)
   - Security scanning
   - Weekly automated scans
   - Pull request analysis

## Badges

All badges are configured and will update automatically:

- ✅ CI/CD Pipeline status
- ✅ Test coverage (100%)
- ✅ Code quality
- ✅ Python version
- ✅ Django version
- ✅ License
- ✅ Test status
- ✅ CodeQL security

## Setting Up Codecov

1. Go to https://codecov.io
2. Sign in with GitHub
3. Add repository: `Sebuliba-Adrian/quorion-b2b-api`
4. Copy the upload token (if needed)
5. Badge will update automatically after first CI run

## Setting Up Code Climate

1. Go to https://codeclimate.com
2. Add repository: `Sebuliba-Adrian/quorion-b2b-api`
3. Get the badge ID from repository settings
4. Update README.md with the badge ID

## Local Development

```bash
# Clone repository
git clone https://github.com/Sebuliba-Adrian/quorion-b2b-api.git
cd quorion-b2b-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
pytest commerce/tests.py --cov=commerce -v

# Run server
python manage.py runserver
```

## Production Deployment

1. Set environment variables
2. Configure PostgreSQL database
3. Run migrations
4. Collect static files
5. Set up web server (nginx + gunicorn)
6. Configure SSL certificates

See `DATABASE_INFO.md` for database configuration details.

