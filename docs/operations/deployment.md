# Deployment Guide

This guide provides comprehensive instructions for deploying the AI Cloud Storage system across different environments.

## Prerequisites

### System Requirements
- Docker 20.10+
- Kubernetes 1.22+
- Helm 3.8+
- kubectl CLI
- Python 3.8+
- Node.js 16+

### Infrastructure Requirements
- Kubernetes cluster
- PostgreSQL database
- Redis instance
- Object storage (S3/MinIO)
- Elasticsearch cluster
- Domain name and SSL certificates

## Environment Setup

### 1. Configuration Files

Create the following configuration files:

```yaml
# config/production.yaml
database:
  host: ${DATABASE_HOST}
  port: 5432
  name: ${DATABASE_NAME}
  user: ${DATABASE_USER}
  password: ${DATABASE_PASSWORD}

redis:
  host: ${REDIS_HOST}
  port: 6379
  password: ${REDIS_PASSWORD}

storage:
  type: s3
  bucket: ${S3_BUCKET}
  region: ${AWS_REGION}
  access_key: ${AWS_ACCESS_KEY}
  secret_key: ${AWS_SECRET_KEY}

ray:
  head_port: 6379
  dashboard_port: 8265
  num_workers: 8
  resources_per_worker:
    cpu: 2
    memory: 4096

security:
  secret_key: ${SECRET_KEY}
  jwt_secret: ${JWT_SECRET}
  allowed_origins:
    - https://your-domain.com

api:
  port: 8000
  workers: 4
  timeout: 60
```

### 2. Environment Variables

Create environment-specific .env files:

```env
# .env.production
DATABASE_HOST=db.example.com
DATABASE_NAME=ai_storage_prod
DATABASE_USER=prod_user
DATABASE_PASSWORD=secure_password

REDIS_HOST=redis.example.com
REDIS_PASSWORD=redis_password

S3_BUCKET=ai-storage-prod
AWS_REGION=us-west-2
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key

SECRET_KEY=production_secret_key
JWT_SECRET=jwt_secret_key
```

## Deployment Steps

### 1. Database Setup

```bash
# Initialize production database
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -f scripts/init.sql

# Run migrations
alembic upgrade head
```

### 2. Docker Images

Build and push Docker images:

```bash
# Build images
docker build -t ai-storage-api:latest -f docker/api/Dockerfile .
docker build -t ai-storage-worker:latest -f docker/worker/Dockerfile .
docker build -t ai-storage-frontend:latest -f docker/frontend/Dockerfile .

# Push to registry
docker push ai-storage-api:latest
docker push ai-storage-worker:latest
docker push ai-storage-frontend:latest
```

### 3. Kubernetes Deployment

Apply Kubernetes manifests:

```bash
# Create namespace
kubectl create namespace ai-storage

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Deploy components
kubectl apply -f k8s/database/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/api/
kubectl apply -f k8s/worker/
kubectl apply -f k8s/frontend/
```

### 4. Ray Cluster Setup

Deploy Ray cluster:

```bash
# Deploy Ray head node
kubectl apply -f k8s/ray/head.yaml

# Deploy Ray workers
kubectl apply -f k8s/ray/worker.yaml
```

### 5. Monitoring Setup

Deploy monitoring stack:

```bash
# Install Prometheus
helm install prometheus prometheus-community/prometheus

# Install Grafana
helm install grafana grafana/grafana

# Apply custom dashboards
kubectl apply -f k8s/monitoring/dashboards/
```

## Verification Steps

### 1. Check Services

```bash
# Verify all pods are running
kubectl get pods -n ai-storage

# Check services
kubectl get services -n ai-storage

# Verify endpoints
kubectl get endpoints -n ai-storage
```

### 2. Health Checks

```bash
# API health check
curl https://api.your-domain.com/health

# Ray dashboard
curl http://ray-dashboard:8265

# Monitor logs
kubectl logs -f deployment/api-deployment -n ai-storage
```

## Scaling

### Horizontal Scaling

```bash
# Scale API pods
kubectl scale deployment api-deployment --replicas=5 -n ai-storage

# Scale workers
kubectl scale deployment worker-deployment --replicas=10 -n ai-storage
```

### Resource Scaling

```yaml
# k8s/api/deployment.yaml
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "2"
    memory: "4Gi"
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME > backup_${TIMESTAMP}.sql
```

### Object Storage Backup

```bash
# Sync to backup bucket
aws s3 sync s3://primary-bucket s3://backup-bucket
```

## Monitoring and Logging

### Prometheus Metrics

```yaml
# prometheus/rules.yaml
groups:
  - name: ai-storage
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
```

### Log Aggregation

```yaml
# fluentd/config.yaml
<match **>
  @type elasticsearch
  host elasticsearch.monitoring
  port 9200
  index_name ai-storage-logs
  type_name log
</match>
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME
   ```

2. **Ray Cluster Issues**
   ```bash
   # Check Ray cluster status
   ray status
   ```

3. **API Performance Issues**
   ```bash
   # Check API metrics
   curl https://api.your-domain.com/metrics
   ```

### Debug Mode

```bash
# Enable debug logging
kubectl set env deployment/api-deployment LOG_LEVEL=DEBUG

# Stream debug logs
kubectl logs -f deployment/api-deployment -n ai-storage
```

## Security Considerations

### SSL/TLS Configuration

```yaml
# ingress/tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-storage-ingress
spec:
  tls:
  - hosts:
    - api.your-domain.com
    secretName: tls-secret
```

### Network Policies

```yaml
# network/policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

## Rollback Procedures

### Version Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/api-deployment -n ai-storage

# Verify rollback
kubectl rollout status deployment/api-deployment -n ai-storage
```

### Database Rollback

```bash
# Revert to specific migration
alembic downgrade <version>
```

## Maintenance

### Regular Tasks

1. **Certificate Renewal**
   ```bash
   # Renew SSL certificates
   certbot renew
   ```

2. **Database Maintenance**
   ```bash
   # Vacuum database
   vacuumdb -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME
   ```

3. **Log Rotation**
   ```bash
   # Configure log rotation
   logrotate /etc/logrotate.d/ai-storage
   ```

## Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [API Documentation](../api/README.md)
- [Monitoring Guide](./monitoring.md)
- [Security Guide](./security.md)
