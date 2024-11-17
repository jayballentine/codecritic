# Email Communication System

## Overview
The email communication system provides robust, subscription-aware email templating and delivery mechanisms with advanced features like rate limiting, retry logic, and queue processing.

## Key Components
- `email_service.py`: Core email service with template rendering, SMTP integration, and queue management
- `email_communication.py`: FastAPI endpoints for email operations

## Features
- Dynamic email templating with Jinja2
- Subscription-aware email personalization
- Reliable email delivery with retry mechanism
- Email queue processing
- Rate limiting to prevent email flooding
- Comprehensive error handling and logging

## Configuration
Configure SMTP settings in your `.env` or configuration file:
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_SENDER=noreply@yourdomain.com
```

## Email Templates
Templates are stored in `app/templates/emails/` and use Jinja2 syntax:
- `review_notification.html`: Repository review results
- `subscription_update.html`: Subscription tier changes

## API Endpoints
- `POST /email/send`: Send an immediate email
- `POST /email/queue`: Queue an email for later processing
- `POST /email/process-queue`: Manually trigger queue processing

## Usage Example
```python
email_request = {
    "recipient": "user@example.com",
    "subject": "Repository Review Complete",
    "template_name": "review_notification",
    "context": {
        "user_name": "John Doe",
        "repository_name": "my-project",
        "code_quality_score": 85
    },
    "subscription_tier": "premium"
}
```

## Testing
Run tests with pytest:
```bash
pytest app/tests/test_email_communication.py
```

## Error Handling
- Comprehensive logging in `app/utils/logger.py`
- Automatic retry for failed email sends
- Queue management for resilient delivery
