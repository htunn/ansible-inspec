"""
Prometheus monitoring and metrics for ansible-inspec server.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from fastapi import Response
import logging

logger = logging.getLogger(__name__)


# Storage operations metrics
storage_operations_total = Counter(
    'storage_operations_total',
    'Total storage operations',
    ['backend', 'operation', 'status']
)

storage_latency_seconds = Histogram(
    'storage_latency_seconds',
    'Storage operation latency in seconds',
    ['backend', 'operation'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

storage_consistency_errors_total = Counter(
    'storage_consistency_errors_total',
    'Total storage consistency errors',
    ['entity_type']
)

# Validation metrics
validation_days_remaining = Gauge(
    'storage_validation_days_remaining',
    'Days remaining in hybrid storage validation period'
)

# Job execution metrics
jobs_total = Counter(
    'jobs_total',
    'Total jobs executed',
    ['status']
)

jobs_duration_seconds = Histogram(
    'jobs_duration_seconds',
    'Job execution duration in seconds',
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

# VCS sync metrics
vcs_sync_total = Counter(
    'vcs_sync_total',
    'Total VCS sync operations',
    ['repository', 'status']
)

vcs_sync_duration_seconds = Histogram(
    'vcs_sync_duration_seconds',
    'VCS sync duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Authentication metrics
auth_requests_total = Counter(
    'auth_requests_total',
    'Total authentication requests',
    ['provider', 'status']
)


def get_metrics() -> Response:
    """
    Get Prometheus metrics
    
    Returns:
        Response with metrics in Prometheus format
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; charset=utf-8"
    )


def record_storage_operation(backend: str, operation: str, status: str, duration: float):
    """
    Record storage operation metrics
    
    Args:
        backend: Storage backend name (file, database, hybrid)
        operation: Operation type (read, write, delete, list)
        status: Operation status (success, error)
        duration: Operation duration in seconds
    """
    storage_operations_total.labels(backend=backend, operation=operation, status=status).inc()
    storage_latency_seconds.labels(backend=backend, operation=operation).observe(duration)


def record_consistency_error(entity_type: str):
    """
    Record storage consistency error
    
    Args:
        entity_type: Type of entity (job_template, job, workflow)
    """
    storage_consistency_errors_total.labels(entity_type=entity_type).inc()


def update_validation_days_remaining(days: int):
    """
    Update validation period days remaining
    
    Args:
        days: Days remaining
    """
    validation_days_remaining.set(days)


def record_job_execution(status: str, duration: float):
    """
    Record job execution metrics
    
    Args:
        status: Job status
        duration: Job duration in seconds
    """
    jobs_total.labels(status=status).inc()
    jobs_duration_seconds.observe(duration)


def record_vcs_sync(repository: str, status: str, duration: float):
    """
    Record VCS sync metrics
    
    Args:
        repository: Repository name
        status: Sync status
        duration: Sync duration in seconds
    """
    vcs_sync_total.labels(repository=repository, status=status).inc()
    vcs_sync_duration_seconds.observe(duration)


def record_auth_request(provider: str, status: str):
    """
    Record authentication request
    
    Args:
        provider: Auth provider (azure_ad, local)
        status: Auth status (success, failed)
    """
    auth_requests_total.labels(provider=provider, status=status).inc()
