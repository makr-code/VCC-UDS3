# UDS3 Security Architecture

**Comprehensive Security Framework for Multi-Database Access Control**

Version: 1.0.0  
Status: Production Ready  
Last Updated: 24. Oktober 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
4. [Row-Level Security (RLS)](#row-level-security-rls)
5. [PKI Integration](#pki-integration)
6. [Audit Logging](#audit-logging)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)
9. [Implementation Guide](#implementation-guide)
10. [Testing](#testing)

---

## Overview

The UDS3 Security Layer provides **enterprise-grade security** for multi-database operations with:

- ✅ **Row-Level Security (RLS)** - Users can only access their own data
- ✅ **Role-Based Access Control (RBAC)** - Least privilege principle enforced
- ✅ **PKI Certificate Authentication** - Integration with VCC PKI system
- ✅ **Comprehensive Audit Logging** - All operations tracked
- ✅ **API Rate Limiting** - DOS protection and fair resource allocation
- ✅ **Zero-Trust Architecture** - Every request authenticated and authorized

### Security Principles

1. **Least Privilege** - Users have minimum necessary permissions
2. **Defense in Depth** - Multiple security layers
3. **Fail Secure** - Default deny on access checks
4. **Audit Everything** - Complete audit trail
5. **Zero Trust** - Never trust, always verify

---

## Security Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        UDS3 Security Layer                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ PKI Auth       │  │ RBAC Engine    │  │ Rate Limiter   │   │
│  │ - Cert Valid   │  │ - 5 Roles      │  │ - Per-User     │   │
│  │ - CRL Check    │  │ - 15 Perms     │  │ - Quotas       │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          Row-Level Security (RLS) Engine               │    │
│  │  - Owner Filtering                                     │    │
│  │  - Permission Checks                                   │    │
│  │  - Metadata Protection                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │               Audit Logging System                      │    │
│  │  - All Operations                                       │    │
│  │  - Success & Failures                                   │    │
│  │  - User Context                                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Secure Database API                            │
│  - create(user, data)                                           │
│  - read(user, filters)                                          │
│  - update(user, id, updates)                                    │
│  - delete(user, id)                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Database Backends                             │
│   PostgreSQL  │  Neo4j  │  CouchDB  │  ChromaDB                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Role-Based Access Control (RBAC)

### User Roles

| Role | Description | Use Case |
|------|-------------|----------|
| **SYSTEM** | Full system access | Internal services only |
| **ADMIN** | Administrative access | System administrators |
| **SERVICE** | Service-to-Service | Inter-service communication |
| **USER** | Standard user | Regular application users |
| **READONLY** | Read-only access | Viewers, auditors |

### Permission Matrix

| Permission | SYSTEM | ADMIN | SERVICE | USER | READONLY |
|------------|--------|-------|---------|------|----------|
| `DATA_READ_OWN` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `DATA_READ_ALL` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `DATA_WRITE_OWN` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `DATA_WRITE_ALL` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `DATA_DELETE_OWN` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `DATA_DELETE_ALL` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `SCHEMA_READ` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `SCHEMA_MODIFY` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ADMIN_BACKUP` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ADMIN_RESTORE` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ADMIN_USERS` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ADMIN_AUDIT` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `BATCH_READ` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `BATCH_WRITE` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `SEARCH_EXECUTE` | ✅ | ✅ | ✅ | ✅ | ❌ |

### Database Permissions

15 granular permissions control database operations:

```python
class DatabasePermission(Enum):
    # Data Operations
    DATA_READ_OWN = "data:read:own"          # ✅ USER
    DATA_READ_ALL = "data:read:all"          # ✅ ADMIN only
    DATA_WRITE_OWN = "data:write:own"        # ✅ USER
    DATA_WRITE_ALL = "data:write:all"        # ✅ ADMIN only
    DATA_DELETE_OWN = "data:delete:own"      # ✅ USER
    DATA_DELETE_ALL = "data:delete:all"      # ✅ ADMIN only
    
    # Schema Operations
    SCHEMA_READ = "schema:read"              # ✅ ALL
    SCHEMA_MODIFY = "schema:modify"          # ✅ ADMIN only
    
    # Admin Operations
    ADMIN_BACKUP = "admin:backup"            # ✅ ADMIN only
    ADMIN_RESTORE = "admin:restore"          # ✅ ADMIN only
    ADMIN_USERS = "admin:users"              # ✅ ADMIN only
    ADMIN_AUDIT = "admin:audit"              # ✅ ADMIN only
    
    # Batch Operations
    BATCH_READ = "batch:read"                # ✅ USER+
    BATCH_WRITE = "batch:write"              # ✅ SERVICE+
    
    # Search & Query
    SEARCH_EXECUTE = "search:execute"        # ✅ USER+
```

---

## Row-Level Security (RLS)

### How RLS Works

1. **Automatic Owner Injection** - All created records get `_owner_user_id` metadata
2. **Filter Enforcement** - Queries automatically filtered by ownership
3. **Permission Checks** - Every operation verified before execution
4. **Metadata Protection** - System metadata cannot be manipulated

### Example: User Can Only See Own Data

```python
# Alice creates documents
secure_api.create(alice, {"title": "Alice's Document"})
secure_api.create(alice, {"title": "Alice's Secret"})

# Bob creates documents
secure_api.create(bob, {"title": "Bob's Document"})

# Alice queries all documents
alice_docs = secure_api.read(alice, {})
# Result: Only Alice's 2 documents (NOT Bob's!)

# Bob queries all documents
bob_docs = secure_api.read(bob, {})
# Result: Only Bob's 1 document (NOT Alice's!)

# Admin queries all documents
admin_docs = secure_api.read(admin, {})
# Result: ALL 3 documents (Alice's + Bob's)
```

### Record Metadata

Every record automatically gets:

```python
{
    "_owner_user_id": "user001",           # Who owns this record
    "_created_by": "alice",                # Username of creator
    "_created_at": "2025-10-24T17:00:00",  # Creation timestamp
    "_updated_by": "alice",                # Last modifier (optional)
    "_updated_at": "2025-10-24T18:00:00"   # Last update (optional)
}
```

### Access Control Flow

```
User Request → Rate Limit Check → Permission Check → RLS Filter
    ↓                  ↓                  ↓               ↓
 Allowed?          Not Exceeded?      Has Permission?   Owns Data?
    ↓                  ↓                  ↓               ↓
   YES ──────────────→ YES ─────────────→ YES ──────────→ YES → ✅ GRANTED
    ↓                  ↓                  ↓               ↓
   NO                 NO                 NO              NO  → ❌ DENIED
    ↓                  ↓                  ↓               ↓
Security           Rate Limit       Permission         Access
Exception          Exception        Exception          Denied (null)
```

---

## PKI Integration

### Certificate-Based Authentication

The UDS3 Security Layer integrates with the **VCC PKI System** for certificate-based authentication:

```python
# Initialize with PKI
security = UDS3SecurityManager(
    pki_ca_cert_path="/path/to/ca.pem",
    enable_pki_auth=True
)

# Authenticate user from client certificate
user = security.authenticate(cert_pem=client_cert)

# User object contains certificate metadata
print(user.certificate_cn)          # Common Name
print(user.certificate_serial)      # Serial number
print(user.certificate_fingerprint) # SHA-256 fingerprint
```

### Certificate Validation

1. **Chain Validation** - Verify certificate signed by trusted CA
2. **Expiration Check** - Ensure certificate still valid
3. **Revocation Check** - Check Certificate Revocation List (CRL)
4. **Role Extraction** - Extract user role from certificate extensions

### User Model with PKI

```python
@dataclass
class User:
    user_id: str
    username: str
    email: str
    role: UserRole
    
    # PKI Certificate Info
    certificate_cn: Optional[str]          # Common Name
    certificate_serial: Optional[str]      # Serial number
    certificate_fingerprint: Optional[str] # SHA-256 fingerprint
    service_name: Optional[str]            # For service accounts
```

---

## Audit Logging

### What Gets Logged

**Every database operation** is logged with:

- ✅ Timestamp
- ✅ User ID & Username
- ✅ User Role
- ✅ Action (read/write/delete/etc.)
- ✅ Resource Type & ID
- ✅ Success/Failure status
- ✅ Error message (if failed)
- ✅ Certificate serial (if PKI auth)

### Audit Log Entry

```python
@dataclass
class AuditLogEntry:
    timestamp: datetime
    user_id: str
    username: str
    role: UserRole
    action: str              # "read", "write", "delete", etc.
    resource_type: str       # "document", "schema", etc.
    resource_id: Optional[str]
    success: bool
    error_message: Optional[str]
    certificate_serial: Optional[str]
```

### Querying Audit Logs

```python
# Admin retrieves audit log
audit_log = secure_api.get_user_audit_log(
    admin_user,
    target_user_id="user001",  # Optional filter
    action="read",              # Optional filter
    start_time=yesterday,       # Optional time range
    end_time=now
)

# Example output
for entry in audit_log:
    print(f"{entry['timestamp']}: {entry['username']} "
          f"{entry['action']} {entry['resource_type']}/{entry['resource_id']} "
          f"→ {'✅' if entry['success'] else '❌'}")
```

### Sample Audit Log

```
2025-10-24 17:30:15: alice read document/doc123 → ✅
2025-10-24 17:30:20: bob read document/doc123 → ❌ Permission denied
2025-10-24 17:30:25: alice write document/doc123 → ✅
2025-10-24 17:30:30: alice delete document/doc123 → ✅
2025-10-24 17:30:35: admin read document/doc456 → ✅
```

---

## Rate Limiting

### Purpose

- ✅ **DOS Protection** - Prevent abuse
- ✅ **Fair Resource Allocation** - Equal access for all
- ✅ **Cost Control** - Limit expensive operations

### Rate Limits by Role

| Role | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| **SYSTEM** | 10,000 | 100,000 | 1,000,000 |
| **ADMIN** | 1,000 | 10,000 | 100,000 |
| **SERVICE** | 1,000 | 10,000 | 100,000 |
| **USER** | 60 | 1,000 | 10,000 |
| **READONLY** | 30 | 500 | 5,000 |

### Rate Limit Enforcement

```python
# Check rate limit before operation
allowed, error = security.check_rate_limit(user)

if not allowed:
    raise SecurityException(f"Rate limit exceeded: {error}")

# Automatic enforcement in SecureDatabaseAPI
secure_api.create(user, data)  # Rate limit checked automatically
```

### Rate Limit Response

```json
{
    "error": "Rate limit exceeded: 60 requests/minute",
    "retry_after": 45,
    "quota": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    }
}
```

---

## Best Practices

### 1. Always Use Secure API

❌ **Don't:**
```python
# Direct database access bypasses security
result = database_api.read({"title": "Document"})
```

✅ **Do:**
```python
# Secure API enforces all security checks
result = secure_api.read(user, {"title": "Document"})
```

### 2. Validate User Context

❌ **Don't:**
```python
# Anonymous access
data = secure_api.read(None, {})
```

✅ **Do:**
```python
# Always provide authenticated user
user = authenticate_user(cert_or_token)
data = secure_api.read(user, {})
```

### 3. Use Least Privilege

❌ **Don't:**
```python
# Grant ADMIN role unnecessarily
user = User("alice", "alice", "alice@vcc.local", UserRole.ADMIN)
```

✅ **Do:**
```python
# Grant minimum necessary role
user = User("alice", "alice", "alice@vcc.local", UserRole.USER)
```

### 4. Monitor Audit Logs

```python
# Regular audit log review
audit_log = secure_api.get_user_audit_log(admin)
failed_attempts = [e for e in audit_log if not e['success']]

if len(failed_attempts) > threshold:
    alert_security_team(failed_attempts)
```

### 5. Handle Security Exceptions

```python
try:
    result = secure_api.delete(user, record_id)
except SecurityException as e:
    logger.warning(f"Security violation: {e}")
    return {"error": "Access denied", "details": str(e)}
```

---

## Implementation Guide

### Quick Start

```python
from security import User, UserRole, UDS3SecurityManager
from database.secure_api import SecureDatabaseAPI

# 1. Initialize security manager
security = UDS3SecurityManager(
    pki_ca_cert_path="/path/to/ca.pem",  # Optional: PKI auth
    enable_pki_auth=True,                 # Optional: Enable PKI
    enable_rate_limiting=True,
    enable_audit_logging=True
)

# 2. Wrap your database API
from database.database_api_postgresql import PostgreSQLDatabaseAPI

pg_api = PostgreSQLDatabaseAPI(config)
secure_pg = SecureDatabaseAPI(pg_api, security)

# 3. Create user (or authenticate via PKI)
user = User(
    user_id="user001",
    username="alice",
    email="alice@vcc.local",
    role=UserRole.USER
)

# 4. Use secure API for all operations
doc_id = secure_pg.create(user, {"title": "My Document"})
docs = secure_pg.read(user, {"title": "My Document"})
secure_pg.update(user, doc_id, {"content": "Updated"})
secure_pg.delete(user, doc_id)
```

### Integration with Existing Code

```python
# Before (insecure)
class MyService:
    def __init__(self, database_api):
        self.db = database_api
    
    def get_documents(self):
        return self.db.read({})  # ❌ No access control!

# After (secure)
class MyService:
    def __init__(self, secure_database_api):
        self.db = secure_database_api
    
    def get_documents(self, user):
        return self.db.read(user, {})  # ✅ Row-level security!
```

---

## Testing

### Security Test Suite

The UDS3 Security Layer includes comprehensive tests:

```bash
# Run all security tests
pytest tests/test_uds3_security.py -v

# Run specific test class
pytest tests/test_uds3_security.py::TestRowLevelSecurity -v
```

### Test Coverage

- ✅ **Row-Level Security** - Users can only access own data
- ✅ **Permission Checks** - Roles have correct permissions
- ✅ **Audit Logging** - All operations logged
- ✅ **Rate Limiting** - Quotas enforced
- ✅ **Privilege Escalation Prevention** - Cannot change ownership
- ✅ **Batch Operations** - Security for bulk operations

### Example Security Test

```python
def test_user_cannot_read_others_data(secure_api, alice, bob):
    """User cannot read data owned by another user"""
    # Alice creates document
    doc_id = secure_api.create(alice, {"title": "Alice's Secret"})
    
    # Bob tries to read Alice's document
    doc = secure_api.read_by_id(bob, doc_id)
    
    # Should be denied
    assert doc is None  # ✅ Access denied
```

---

## Security Checklist

Use this checklist for secure UDS3 deployments:

- [ ] **PKI Integration**
  - [ ] PKI CA certificate configured
  - [ ] CRL endpoint accessible
  - [ ] Certificate validation enabled

- [ ] **Access Control**
  - [ ] All database APIs wrapped with SecureDatabaseAPI
  - [ ] User context required for all operations
  - [ ] Least privilege roles assigned

- [ ] **Audit Logging**
  - [ ] Audit logging enabled
  - [ ] Logs regularly reviewed
  - [ ] Failed access attempts monitored

- [ ] **Rate Limiting**
  - [ ] Rate limits configured per role
  - [ ] DOS protection active
  - [ ] Quota violations logged

- [ ] **Testing**
  - [ ] Security tests passing
  - [ ] Penetration testing completed
  - [ ] Privilege escalation tests passed

- [ ] **Monitoring**
  - [ ] Security metrics tracked
  - [ ] Alerting configured
  - [ ] Incident response plan ready

---

## Support & Contact

For security issues or questions:

- **Security Team**: security@vcc.local
- **Documentation**: `/docs/SECURITY.md`
- **Issue Tracker**: https://github.com/makr-code/VCC-UDS3/issues

---

**Last Updated**: 24. Oktober 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
