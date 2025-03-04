from setuptools import setup, find_packages

setup(
    name="ai-cloud-storage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "sqlalchemy>=1.4.0",
        "asyncpg>=0.24.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.5",
        "minio>=7.1.0",
        "redis>=4.0.0",
        "transformers>=4.11.0",
        "torch>=1.9.0",
        "pytest>=6.2.5",
        "pytest-asyncio>=0.15.1",
        "pytest-cov>=2.12.1",
        "httpx>=0.18.2",
    ],
    python_requires=">=3.9",
)
