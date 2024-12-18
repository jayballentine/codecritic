from setuptools import setup, find_packages

setup(
    name="codecritic",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.95.1",
        "uvicorn==0.22.0",
        "sqlalchemy==1.4.46",
        "pydantic==1.10.7",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "jinja2==3.1.2",
        "pytest==8.2.0",
        "pytest-asyncio==0.23.5",
        "requests==2.28.2",
        "python-multipart==0.0.6",
        "email-validator==2.0.0",
        "supabase==1.0.3",
        "python-dotenv==1.0.0",
        "PyJWT==2.7.0",
        "pyyaml==6.0.1",
        "bcrypt==4.0.1"
    ],
)
