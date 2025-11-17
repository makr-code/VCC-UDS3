# UDS3 Deployment Examples

This directory contains deployment examples for various environments.

## Quick Start

Choose your deployment scenario:

- **Local Development:** `docker-compose-dev.yml`
- **Production (Docker):** `docker-compose-prod.yml`
- **Kubernetes:** `k8s/`
- **Configuration Templates:** `configs/`

## Examples

### 1. Local Development with Docker Compose

```bash
cd examples
docker-compose -f docker-compose-dev.yml up
```

This starts:
- PostgreSQL with PostGIS
- Neo4j
- ChromaDB
- CouchDB
- UDS3 API (development mode)

### 2. Production Deployment

```bash
cd examples
docker-compose -f docker-compose-prod.yml up -d
```

### 3. Kubernetes Deployment

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

## Configuration

See `configs/` for example configurations for each backend.
