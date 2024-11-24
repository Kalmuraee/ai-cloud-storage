# Security Guide

This guide outlines the security measures and best practices implemented in the AI Cloud Storage system.

## Security Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   WAF/CDN    │───►│   Gateway    │───►│    Auth      │
└──────────────┘    └──────────────┘    └──────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐    ┌──────────────┐
                    │   Services   │    │  JWT/OAuth   │
                    └──────────────┘    └──────────────┘
```

## Authentication & Authorization

### 1. JWT Implementation

```python
# auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 2. OAuth Configuration

```python
# auth/oauth.py
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "read": "Read access",
        "write": "Write access",
        "admin": "Admin access"
    }
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data
```

## API Security

### 1. Rate Limiting

```python
# middleware/rate_limit.py
from fastapi import HTTPException
from redis import Redis
from datetime import timedelta

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds

    async def check_rate_limit(self, client_id: str):
        current = self.redis.get(f"rate_limit:{client_id}")
        if current and int(current) > self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        pipe = self.redis.pipeline()
        pipe.incr(f"rate_limit:{client_id}")
        pipe.expire(f"rate_limit:{client_id}", self.window)
        pipe.execute()
```

### 2. Input Validation

```python
# models/validation.py
from pydantic import BaseModel, validator
import re

class Document(BaseModel):
    title: str
    content: str
    metadata: dict

    @validator('title')
    def title_must_be_valid(cls, v):
        if not re.match("^[a-zA-Z0-9_-]{3,50}$", v):
            raise ValueError('Invalid title format')
        return v

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v
```

## Network Security

### 1. Network Policies

```yaml
# k8s/network/policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

### 2. TLS Configuration

```yaml
# k8s/ingress/tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

## Data Security

### 1. Encryption at Rest

```python
# storage/encryption.py
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self, key: str):
        self.fernet = Fernet(base64.b64encode(key.encode()))

    def encrypt_data(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)
```

### 2. Secure File Storage

```python
# storage/files.py
from typing import BinaryIO
import boto3
from botocore.config import Config

class SecureStorage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            config=Config(signature_version='s3v4')
        )

    def upload_file(self, file: BinaryIO, bucket: str, key: str):
        self.s3.upload_fileobj(
            file,
            bucket,
            key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'ACL': 'private'
            }
        )
```

## Security Monitoring

### 1. Audit Logging

```python
# logging/audit.py
import logging
from datetime import datetime

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)

    def log_access(self, user_id: str, resource: str, action: str):
        self.logger.info({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'type': 'access'
        })

    def log_change(self, user_id: str, resource: str, change: dict):
        self.logger.info({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource': resource,
            'change': change,
            'type': 'change'
        })
```

### 2. Security Alerts

```yaml
# prometheus/alerts/security.yaml
groups:
- name: security
  rules:
  - alert: HighLoginFailures
    expr: rate(login_failures_total[5m]) > 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High rate of login failures detected
      
  - alert: UnauthorizedAccessAttempts
    expr: rate(unauthorized_access_total[5m]) > 5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: Multiple unauthorized access attempts detected
```

## Compliance

### 1. Data Retention

```python
# compliance/retention.py
from datetime import datetime, timedelta

class DataRetention:
    def __init__(self, storage_client):
        self.storage = storage_client
        self.retention_periods = {
            'logs': timedelta(days=90),
            'documents': timedelta(years=7),
            'backups': timedelta(days=30)
        }

    async def enforce_retention(self):
        for data_type, period in self.retention_periods.items():
            cutoff_date = datetime.utcnow() - period
            await self.delete_old_data(data_type, cutoff_date)
```

### 2. Access Control

```python
# compliance/access.py
from enum import Enum
from typing import List

class AccessLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class AccessControl:
    def __init__(self):
        self.access_matrix = {
            'user': [AccessLevel.READ],
            'editor': [AccessLevel.READ, AccessLevel.WRITE],
            'admin': [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN]
        }

    def check_access(self, user_role: str, required_level: AccessLevel) -> bool:
        if user_role not in self.access_matrix:
            return False
        return required_level in self.access_matrix[user_role]
```

## Security Best Practices

### 1. Password Policies

```python
# auth/password.py
import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password_strength(password: str) -> bool:
    if len(password) < 12:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    if not re.search("[^A-Za-z0-9]", password):
        return False
    return True

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

### 2. Session Management

```python
# auth/session.py
from redis import Redis
from uuid import uuid4
from datetime import timedelta

class SessionManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.session_timeout = timedelta(hours=1)

    def create_session(self, user_id: str) -> str:
        session_id = str(uuid4())
        self.redis.setex(
            f"session:{session_id}",
            self.session_timeout,
            user_id
        )
        return session_id

    def validate_session(self, session_id: str) -> str:
        return self.redis.get(f"session:{session_id}")

    def invalidate_session(self, session_id: str):
        self.redis.delete(f"session:{session_id}")
```

## Related Documentation

- [Deployment Guide](./deployment.md)
- [Monitoring Guide](./monitoring.md)
- [Architecture Overview](../architecture/overview.md)
- [API Documentation](../api/README.md)
