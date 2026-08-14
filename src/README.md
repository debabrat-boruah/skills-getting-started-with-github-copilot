# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                                  | Description                                                         |
| ------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                            | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`         | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/participants/{email}`                       | Remove a participant from an activity                               |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

## Running Tests

The project includes a comprehensive test suite using pytest.

### Install test dependencies:

```bash
pip install pytest
```

### Run all tests:

```bash
pytest tests/ -v
```

### Run specific test file:

```bash
pytest tests/test_api.py -v
pytest tests/test_edge_cases.py -v
```

### Run with coverage report:

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

## Test Structure

- `tests/conftest.py` — Pytest fixtures for app, client, and test data isolation
- `tests/test_api.py` — Core endpoint tests (signup, delete, retrieve activities)
- `tests/test_edge_cases.py` — Edge cases, URL encoding, state consistency, boundary conditions

The test suite uses fixtures to isolate test data, ensuring each test runs with a fresh copy of the activities data. This prevents test interference and ensures reliable, repeatable results.
