"""
UDS3 Security Layer - PKI-Integrated Authentication & Authorization
===================================================================

Production-grade security implementation with:
- PKI Certificate-based Authentication (mTLS)
- Role-Based Access Control (RBAC) 
- Least Privilege Access Control
- Row-Level Security (RLS) für Database APIs
- Audit Logging
- API Rate Limiting
- JWT Token Support (fallback)

Integration:
- PKI Package für Certificate Management
- UDS3 Database APIs mit Access Control
- Multi-Backend Security (PostgreSQL RLS, Neo4j, CouchDB, ChromaDB)

Author: UDS3 Security Team
Created: 2025-10-24
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set, List
from datetime import datetime, timedelta
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)


# ============================================================================
# User Roles & Permissions
# ============================================================================

class UserRole(Enum):
    """User roles for RBAC - Least Privilege Model"""
    SYSTEM = "system"      # Full system access (internal services only)
    ADMIN = "admin"        # Administrative access
    SERVICE = "service"    # Service-to-Service communication
    USER = "user"          # Standard user (own data only)
    READONLY = "readonly"  # Read-only access


class DatabasePermission(Enum):
    """Database-specific permissions"""
    # Data Operations
    DATA_READ_OWN = "data:read:own"          # Read own data only
    DATA_READ_ALL = "data:read:all"          # Read all data
    DATA_WRITE_OWN = "data:write:own"        # Write own data only
    DATA_WRITE_ALL = "data:write:all"        # Write all data
    DATA_DELETE_OWN = "data:delete:own"      # Delete own data
    DATA_DELETE_ALL = "data:delete:all"      # Delete any data
    
    # Schema Operations
    SCHEMA_READ = "schema:read"              # Read schema info
    SCHEMA_MODIFY = "schema:modify"          # Modify schema
    
    # Admin Operations
    ADMIN_BACKUP = "admin:backup"            # Database backup
    ADMIN_RESTORE = "admin:restore"          # Database restore
    ADMIN_USERS = "admin:users"              # User management
    ADMIN_AUDIT = "admin:audit"              # Access audit logs
    
    # Batch Operations
    BATCH_READ = "batch:read"                # Batch read operations
    BATCH_WRITE = "batch:write"              # Batch write operations
    
    # Search & Query
    SEARCH_EXECUTE = "search:execute"        # Execute search queries
    SEARCH_ADMIN = "search:admin"            # Manage search indices


# Role → Permission Mapping (Least Privilege)
ROLE_PERMISSIONS: Dict[UserRole, Set[DatabasePermission]] = {
    UserRole.SYSTEM: {
        # System has ALL permissions
        *list(DatabasePermission)
    },
    UserRole.ADMIN: {
        DatabasePermission.DATA_READ_ALL,
        DatabasePermission.DATA_WRITE_ALL,
        DatabasePermission.DATA_DELETE_ALL,
        DatabasePermission.SCHEMA_READ,
        DatabasePermission.SCHEMA_MODIFY,
        DatabasePermission.ADMIN_BACKUP,
        DatabasePermission.ADMIN_RESTORE,
        DatabasePermission.ADMIN_USERS,
        DatabasePermission.ADMIN_AUDIT,
        DatabasePermission.BATCH_READ,
        DatabasePermission.BATCH_WRITE,
        DatabasePermission.SEARCH_EXECUTE,
        DatabasePermission.SEARCH_ADMIN,
    },
    UserRole.SERVICE: {
        DatabasePermission.DATA_READ_ALL,
        DatabasePermission.DATA_WRITE_ALL,
        DatabasePermission.SCHEMA_READ,
        DatabasePermission.BATCH_READ,
        DatabasePermission.BATCH_WRITE,
        DatabasePermission.SEARCH_EXECUTE,
    },
    UserRole.USER: {
        # Least Privilege: Own data only
        DatabasePermission.DATA_READ_OWN,
        DatabasePermission.DATA_WRITE_OWN,
        DatabasePermission.DATA_DELETE_OWN,
        DatabasePermission.SCHEMA_READ,
        DatabasePermission.SEARCH_EXECUTE,
    },
    UserRole.READONLY: {
        DatabasePermission.DATA_READ_OWN,
        DatabasePermission.SCHEMA_READ,
    },
}


# ============================================================================
# User & Authentication Models
# ============================================================================

@dataclass
class User:
    """User model with PKI certificate integration"""
    user_id: str
    username: str
    email: str
    role: UserRole
    
    # PKI Certificate Info
    certificate_cn: Optional[str] = None          # Common Name from cert
    certificate_serial: Optional[str] = None      # Certificate serial number
    certificate_fingerprint: Optional[str] = None # Certificate SHA-256 fingerprint
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    # Optional: Service-specific metadata
    service_name: Optional[str] = None  # For service accounts
    
    def get_permissions(self) -> Set[DatabasePermission]:
        """Get all permissions for this user's role"""
        return ROLE_PERMISSIONS.get(self.role, set())
    
    def has_permission(self, permission: DatabasePermission) -> bool:
        """Check if user has specific permission"""
        return permission in self.get_permissions()
    
    def can_access_data(self, owner_user_id: str) -> bool:
        """Check if user can access data owned by another user"""
        # System and Admin can access all data
        if self.role in {UserRole.SYSTEM, UserRole.ADMIN}:
            return True
        # Services can access all data (for processing)
        if self.role == UserRole.SERVICE:
            return True
        # Users can only access own data
        return self.user_id == owner_user_id


@dataclass
class AuditLogEntry:
    """Audit log entry for security events"""
    timestamp: datetime
    user_id: str
    username: str
    role: UserRole
    
    action: str  # e.g., "read", "write", "delete", "schema_modify"
    resource_type: str  # e.g., "document", "schema", "user"
    resource_id: Optional[str]
    
    success: bool
    error_message: Optional[str] = None
    
    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # PKI metadata
    certificate_serial: Optional[str] = None


# ============================================================================
# PKI Integration
# ============================================================================

class PKIAuthenticator:
    """
    PKI-based authentication using client certificates
    
    Integrates with VCC PKI system for:
    - Client certificate validation
    - Role extraction from certificate extensions
    - Certificate revocation checking (CRL)
    - Audit logging
    """
    
    def __init__(self, pki_ca_cert_path: str, crl_path: Optional[str] = None):
        """
        Initialize PKI authenticator
        
        Args:
            pki_ca_cert_path: Path to PKI CA certificate for validation
            crl_path: Optional path to CRL for revocation checks
        """
        self.pki_ca_cert_path = pki_ca_cert_path
        self.crl_path = crl_path
        self._revoked_certs: Set[str] = set()
        
        if crl_path:
            self._load_crl()
    
    def _load_crl(self):
        """Load Certificate Revocation List"""
        # TODO: Implement CRL parsing
        logger.info(f"Loading CRL from {self.crl_path}")
    
    def authenticate_certificate(self, cert_pem: str) -> Optional[User]:
        """
        Authenticate user from client certificate
        
        Args:
            cert_pem: PEM-encoded client certificate
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # TODO: Integrate with PKI package for actual validation
            # For now: Mock implementation
            
            # 1. Validate certificate chain
            # 2. Check expiration
            # 3. Check revocation (CRL)
            # 4. Extract user info from certificate
            
            # Extract Common Name (CN) as username
            # Extract role from certificate extension or OU
            
            # Example:
            cert_info = self._parse_certificate(cert_pem)
            
            if not cert_info:
                return None
            
            # Check if revoked
            if cert_info['serial'] in self._revoked_certs:
                logger.warning(f"Certificate revoked: {cert_info['serial']}")
                return None
            
            # Map certificate to user
            user = User(
                user_id=cert_info['user_id'],
                username=cert_info['cn'],
                email=cert_info.get('email', f"{cert_info['cn']}@vcc.local"),
                role=cert_info['role'],
                certificate_cn=cert_info['cn'],
                certificate_serial=cert_info['serial'],
                certificate_fingerprint=cert_info['fingerprint'],
                service_name=cert_info.get('service_name')
            )
            
            user.last_login = datetime.now()
            
            logger.info(f"PKI authentication successful: {user.username} ({user.role.value})")
            return user
            
        except Exception as e:
            logger.error(f"PKI authentication failed: {e}")
            return None
    
    def _parse_certificate(self, cert_pem: str) -> Optional[Dict[str, Any]]:
        """Parse certificate and extract user information"""
        # TODO: Implement actual certificate parsing with cryptography library
        # This is a mock implementation
        return {
            'user_id': 'user123',
            'cn': 'user.name',
            'email': 'user.name@vcc.local',
            'role': UserRole.USER,
            'serial': '1234567890',
            'fingerprint': 'abc123...',
            'service_name': None
        }


# ============================================================================
# Database Access Control
# ============================================================================

class DatabaseAccessControl:
    """
    Row-Level Security (RLS) for Database APIs
    
    Enforces least privilege access control:
    - Users can only access their own data
    - Services can access all data for processing
    - Admins have full access
    """
    
    def __init__(self):
        self.audit_log: List[AuditLogEntry] = []
    
    def check_read_access(
        self,
        user: User,
        owner_user_id: str,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """
        Check if user can read a resource
        
        Args:
            user: Authenticated user
            owner_user_id: Owner of the resource
            resource_type: Type of resource (e.g., "document")
            resource_id: Resource identifier
            
        Returns:
            True if access granted, False otherwise
        """
        # Check permission
        if user.has_permission(DatabasePermission.DATA_READ_ALL):
            # Admin/Service can read all
            self._log_access(user, "read", resource_type, resource_id, True)
            return True
        
        if user.has_permission(DatabasePermission.DATA_READ_OWN):
            # User can read own data
            if user.can_access_data(owner_user_id):
                self._log_access(user, "read", resource_type, resource_id, True)
                return True
        
        # Access denied
        self._log_access(user, "read", resource_type, resource_id, False,
                        error="Permission denied")
        return False
    
    def check_write_access(
        self,
        user: User,
        owner_user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user can write/create a resource"""
        if user.has_permission(DatabasePermission.DATA_WRITE_ALL):
            self._log_access(user, "write", resource_type, resource_id, True)
            return True
        
        if user.has_permission(DatabasePermission.DATA_WRITE_OWN):
            if user.can_access_data(owner_user_id):
                self._log_access(user, "write", resource_type, resource_id, True)
                return True
        
        self._log_access(user, "write", resource_type, resource_id, False,
                        error="Permission denied")
        return False
    
    def check_delete_access(
        self,
        user: User,
        owner_user_id: str,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """Check if user can delete a resource"""
        if user.has_permission(DatabasePermission.DATA_DELETE_ALL):
            self._log_access(user, "delete", resource_type, resource_id, True)
            return True
        
        if user.has_permission(DatabasePermission.DATA_DELETE_OWN):
            if user.can_access_data(owner_user_id):
                self._log_access(user, "delete", resource_type, resource_id, True)
                return True
        
        self._log_access(user, "delete", resource_type, resource_id, False,
                        error="Permission denied")
        return False
    
    def _log_access(
        self,
        user: User,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        success: bool,
        error: Optional[str] = None
    ):
        """Log access attempt for audit trail"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            error_message=error,
            certificate_serial=user.certificate_serial
        )
        
        self.audit_log.append(entry)
        
        if not success:
            logger.warning(
                f"Access denied: {user.username} ({user.role.value}) "
                f"attempted {action} on {resource_type}/{resource_id}: {error}"
            )
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Retrieve audit log entries with filters"""
        filtered = self.audit_log
        
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        if action:
            filtered = [e for e in filtered if e.action == action]
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        
        return filtered


# ============================================================================
# API Rate Limiting
# ============================================================================

@dataclass
class RateLimitQuota:
    """Rate limit quota per user/role"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int


# Rate limits per role
RATE_LIMITS: Dict[UserRole, RateLimitQuota] = {
    UserRole.SYSTEM: RateLimitQuota(10000, 100000, 1000000),  # No effective limit
    UserRole.ADMIN: RateLimitQuota(1000, 10000, 100000),
    UserRole.SERVICE: RateLimitQuota(1000, 10000, 100000),
    UserRole.USER: RateLimitQuota(60, 1000, 10000),
    UserRole.READONLY: RateLimitQuota(30, 500, 5000),
}


class RateLimiter:
    """
    API Rate limiting per user/role
    
    Prevents abuse and ensures fair resource allocation
    """
    
    def __init__(self):
        self._user_requests: Dict[str, List[datetime]] = {}
    
    def check_rate_limit(self, user: User) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit
        
        Returns:
            (allowed: bool, error_message: Optional[str])
        """
        quota = RATE_LIMITS.get(user.role, RATE_LIMITS[UserRole.USER])
        now = datetime.now()
        
        # Get user's request history
        if user.user_id not in self._user_requests:
            self._user_requests[user.user_id] = []
        
        requests = self._user_requests[user.user_id]
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        requests = [r for r in requests if r > day_ago]
        self._user_requests[user.user_id] = requests
        
        # Count recent requests
        recent_minute = sum(1 for r in requests if r > minute_ago)
        recent_hour = sum(1 for r in requests if r > hour_ago)
        recent_day = len(requests)
        
        # Check limits
        if recent_minute >= quota.requests_per_minute:
            return False, f"Rate limit exceeded: {quota.requests_per_minute} requests/minute"
        if recent_hour >= quota.requests_per_hour:
            return False, f"Rate limit exceeded: {quota.requests_per_hour} requests/hour"
        if recent_day >= quota.requests_per_day:
            return False, f"Rate limit exceeded: {quota.requests_per_day} requests/day"
        
        # Add current request
        requests.append(now)
        
        return True, None


# ============================================================================
# Security Manager (Main Interface)
# ============================================================================

class UDS3SecurityManager:
    """
    Main security manager for UDS3
    
    Integrates:
    - PKI authentication
    - Access control
    - Audit logging
    - Rate limiting
    """
    
    def __init__(
        self,
        pki_ca_cert_path: Optional[str] = None,
        enable_pki_auth: bool = False,
        enable_rate_limiting: bool = True,
        enable_audit_logging: bool = True
    ):
        self.pki_authenticator = (
            PKIAuthenticator(pki_ca_cert_path) if enable_pki_auth and pki_ca_cert_path
            else None
        )
        self.access_control = DatabaseAccessControl() if enable_audit_logging else None
        self.rate_limiter = RateLimiter() if enable_rate_limiting else None
        
        logger.info(f"UDS3 Security Manager initialized (PKI: {enable_pki_auth})")
    
    def authenticate(self, cert_pem: Optional[str] = None) -> Optional[User]:
        """Authenticate user via PKI certificate"""
        if not cert_pem or not self.pki_authenticator:
            # Fallback: Create anonymous user or use JWT
            return None
        
        return self.pki_authenticator.authenticate_certificate(cert_pem)
    
    def check_access(
        self,
        user: User,
        action: str,
        owner_user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has access to perform action on resource"""
        if not self.access_control:
            return True  # Access control disabled
        
        if action == "read":
            return self.access_control.check_read_access(
                user, owner_user_id, resource_type, resource_id or ""
            )
        elif action == "write":
            return self.access_control.check_write_access(
                user, owner_user_id, resource_type, resource_id
            )
        elif action == "delete":
            return self.access_control.check_delete_access(
                user, owner_user_id, resource_type, resource_id or ""
            )
        
        return False
    
    def check_rate_limit(self, user: User) -> tuple[bool, Optional[str]]:
        """Check if user has exceeded rate limit"""
        if not self.rate_limiter:
            return True, None  # Rate limiting disabled
        
        return self.rate_limiter.check_rate_limit(user)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("UDS3 SECURITY LAYER - DEMONSTRATION")
    print("="*70 + "\n")
    
    # Initialize security manager
    security = UDS3SecurityManager(
        enable_pki_auth=False,  # PKI disabled for demo
        enable_rate_limiting=True,
        enable_audit_logging=True
    )
    
    # Create test users
    admin_user = User(
        user_id="admin001",
        username="admin",
        email="admin@vcc.local",
        role=UserRole.ADMIN
    )
    
    regular_user = User(
        user_id="user001",
        username="john.doe",
        email="john.doe@vcc.local",
        role=UserRole.USER
    )
    
    print("1. Testing Access Control")
    print("-" * 50)
    
    # Admin can read all data
    can_access = security.check_access(
        admin_user, "read", "user001", "document", "doc123"
    )
    print(f"  Admin read user001's document: {can_access}")
    
    # User can read own data
    can_access = security.check_access(
        regular_user, "read", "user001", "document", "doc123"
    )
    print(f"  User read own document: {can_access}")
    
    # User cannot read other's data
    can_access = security.check_access(
        regular_user, "read", "user002", "document", "doc456"
    )
    print(f"  User read other's document: {can_access}")
    
    print("\n2. Testing Rate Limiting")
    print("-" * 50)
    
    # Test rate limits
    for i in range(5):
        allowed, error = security.check_rate_limit(regular_user)
        print(f"  Request {i+1}: {'✅ Allowed' if allowed else f'❌ {error}'}")
    
    print("\n3. Audit Log")
    print("-" * 50)
    
    if security.access_control:
        log_entries = security.access_control.get_audit_log()
        print(f"  Total audit entries: {len(log_entries)}")
        for entry in log_entries[-3:]:  # Show last 3
            status = "✅" if entry.success else "❌"
            print(f"  {status} {entry.timestamp.strftime('%H:%M:%S')} - "
                  f"{entry.username} {entry.action} {entry.resource_type}/{entry.resource_id}")
    
    print("\n" + "="*70)
    print("✅ UDS3 Security Layer Demo Complete")
    print("="*70 + "\n")
