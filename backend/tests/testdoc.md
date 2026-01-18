# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_security.py

# Run only unit tests
pytest -m unit

# Run only security tests
pytest -m security

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run specific test function
pytest backend/tests/test_models.py::TestUserModel::test_create_user