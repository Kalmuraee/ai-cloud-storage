# Monitoring Guide

This guide details the monitoring setup and practices for the AI Cloud Storage system.

## Monitoring Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Services   │───►│  Prometheus  │───►│   Grafana    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Metrics    │    │   Alerting   │    │  Dashboards  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Key Metrics

### 1. System Metrics

#### CPU Usage
```yaml
# prometheus/rules/system.yaml
- record: instance:cpu_usage_percent
  expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

#### Memory Usage
```yaml
# prometheus/rules/system.yaml
- record: instance:memory_usage_percent
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
```

#### Disk Usage
```yaml
# prometheus/rules/system.yaml
- record: instance:disk_usage_percent
  expr: 100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)
```

### 2. Application Metrics

#### API Latency
```yaml
# prometheus/rules/api.yaml
- record: api:request_duration_seconds
  expr: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

#### Error Rate
```yaml
# prometheus/rules/api.yaml
- record: api:error_rate
  expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

#### Request Rate
```yaml
# prometheus/rules/api.yaml
- record: api:request_rate
  expr: sum(rate(http_requests_total[5m])) by (endpoint)
```

### 3. Ray Cluster Metrics

#### Worker Utilization
```yaml
# prometheus/rules/ray.yaml
- record: ray:worker_utilization
  expr: avg(ray_worker_utilization)
```

#### Task Throughput
```yaml
# prometheus/rules/ray.yaml
- record: ray:task_throughput
  expr: sum(rate(ray_tasks_completed_total[5m]))
```

## Alert Rules

### 1. System Alerts

```yaml
# prometheus/alerts/system.yaml
groups:
- name: system
  rules:
  - alert: HighCPUUsage
    expr: instance:cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High CPU usage on {{ $labels.instance }}
      
  - alert: HighMemoryUsage
    expr: instance:memory_usage_percent > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High memory usage on {{ $labels.instance }}
      
  - alert: DiskSpaceLow
    expr: instance:disk_usage_percent > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Low disk space on {{ $labels.instance }}
```

### 2. Application Alerts

```yaml
# prometheus/alerts/application.yaml
groups:
- name: application
  rules:
  - alert: HighErrorRate
    expr: api:error_rate > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      
  - alert: APILatencyHigh
    expr: api:request_duration_seconds > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: API latency is high
      
  - alert: HighRequestRate
    expr: api:request_rate > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Unusual high request rate detected
```

### 3. Ray Cluster Alerts

```yaml
# prometheus/alerts/ray.yaml
groups:
- name: ray
  rules:
  - alert: LowWorkerUtilization
    expr: ray:worker_utilization < 0.3
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: Ray workers are underutilized
      
  - alert: HighTaskFailureRate
    expr: rate(ray_tasks_failed_total[5m]) / rate(ray_tasks_completed_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High task failure rate in Ray cluster
```

## Grafana Dashboards

### 1. System Overview

```json
{
  "title": "System Overview",
  "panels": [
    {
      "title": "CPU Usage",
      "type": "graph",
      "targets": [
        {
          "expr": "instance:cpu_usage_percent"
        }
      ]
    },
    {
      "title": "Memory Usage",
      "type": "graph",
      "targets": [
        {
          "expr": "instance:memory_usage_percent"
        }
      ]
    }
  ]
}
```

### 2. API Performance

```json
{
  "title": "API Performance",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "api:request_rate"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "api:error_rate"
        }
      ]
    }
  ]
}
```

### 3. Ray Cluster Performance

```json
{
  "title": "Ray Cluster",
  "panels": [
    {
      "title": "Worker Utilization",
      "type": "graph",
      "targets": [
        {
          "expr": "ray:worker_utilization"
        }
      ]
    },
    {
      "title": "Task Throughput",
      "type": "graph",
      "targets": [
        {
          "expr": "ray:task_throughput"
        }
      ]
    }
  ]
}
```

## Log Aggregation

### 1. Fluentd Configuration

```yaml
# fluentd/config.yaml
<source>
  @type tail
  path /var/log/ai-storage/*.log
  pos_file /var/log/ai-storage/fluentd.pos
  tag ai-storage
  <parse>
    @type json
  </parse>
</source>

<match ai-storage.**>
  @type elasticsearch
  host elasticsearch.monitoring
  port 9200
  index_name ai-storage-${tag}-%Y%m%d
  include_timestamp true
</match>
```

### 2. Log Format

```python
# logging/config.py
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ai-storage/application.log',
            'formatter': 'json',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        'ai_storage': {
            'handlers': ['file'],
            'level': 'INFO'
        }
    }
}
```

## Monitoring Best Practices

### 1. Metric Collection

- Use consistent naming conventions
- Keep cardinality under control
- Monitor both system and business metrics
- Set appropriate scrape intervals

### 2. Alert Configuration

- Set meaningful thresholds
- Avoid alert fatigue
- Include clear resolution steps
- Use appropriate severity levels

### 3. Dashboard Organization

- Group related metrics
- Use consistent time ranges
- Include documentation
- Make dashboards actionable

## Related Documentation

- [Deployment Guide](./deployment.md)
- [Architecture Overview](../architecture/overview.md)
- [Security Guide](./security.md)
- [Operations Guide](./operations.md)
