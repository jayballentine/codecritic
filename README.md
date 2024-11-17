# CodeCritic

## Project Overview

CodeCritic is an intelligent code review platform designed to demystify software development quality for non-technical stakeholders. By leveraging advanced AI and machine learning technologies, CodeCritic transforms complex code analysis into actionable insights, enabling business leaders, project managers, and investors to understand and mitigate software development risks without deep technical expertise.

## Key Features

### 1. GitHub-Based Repository Review
- Seamlessly analyze code repositories directly from GitHub links
- Comprehensive code quality assessment using advanced AI algorithms
- Identify potential vulnerabilities, code smells, and architectural risks

### 2. OAuth Authentication
- Secure login using GitHub credentials
- Role-based access control
- Protect sensitive project information with industry-standard authentication

### 3. Subscription Management
- Flexible subscription tiers for different project needs
- Easy upgrade and downgrade options
- Transparent pricing based on repository complexity and analysis depth

### 4. Email Reporting
- Automated, scheduled code review reports
- Customizable notification preferences
- Detailed insights delivered directly to stakeholders' inboxes

## Project Structure

The project follows a modular architecture with clear separation of concerns:
- `api/`: REST endpoints and route handlers
- `models/`: Database models and schemas
- `services/`: Business logic implementation
- `db/`: Database configuration and migrations
- `utils/`: Helper functions and utilities
- `tests/`: Unit and integration tests

## Development Setup

### Prerequisites
- Python 3.9+
- pip
- GitHub account (for OAuth)

### Local Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/codecritic.git
cd codecritic
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your GitHub OAuth and database credentials
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Testing

Ensure code quality by running the test suite:
```bash
pytest
```

## API Documentation

Comprehensive API documentation is available at `/docs` when the server is running.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

[MIT License](LICENSE)
