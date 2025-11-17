# Example PostgreSQL Configuration for UDS3

## Connection Settings

```python
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "uds3",
    "user": "uds3_user",
    "password": "secure_password_here",
    "sslmode": "require",  # Production: require, prefer, or verify-full
    "application_name": "UDS3",
    "connect_timeout": 10,
    "options": "-c search_path=public,uds3"
}
```

## PostGIS Extension

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify installation
SELECT PostGIS_Version();
```

## Connection Pool

```python
# Recommended connection pool settings
POOL_CONFIG = {
    "min_size": 2,
    "max_size": 10,
    "max_queries": 50000,
    "max_inactive_connection_lifetime": 300.0
}
```

## Environment Variables

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=uds3
export POSTGRES_USER=uds3_user
export POSTGRES_PASSWORD=secure_password_here
```
