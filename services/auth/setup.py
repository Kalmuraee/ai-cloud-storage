from setuptools import setup, find_packages

setup(
    name="auth-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pydantic-settings",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "alembic",
        "psycopg2-binary",
        "emails",
        "jinja2",
        "redis",
        "python-dateutil",
    ],
)