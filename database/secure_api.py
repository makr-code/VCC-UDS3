"""
UDS3 Database API Security Wrapper
==================================

Secure wrapper for all database operations with:
- Row-Level Security (RLS)
- Least Privilege Access Control
- Audit Logging
- Automatic owner_user_id injection

Usage:
    from database.secure_api import SecureDatabaseAPI
    
    secure_api = SecureDatabaseAPI(underlying_api, security_manager)
    
    # All operations require user context
    result = secure_api.create(user, data)
    records = secure_api.read(user, filters)
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Import security layer
try:
    from ..security import (
        User, UserRole, DatabasePermission, 
        UDS3SecurityManager, DatabaseAccessControl
    )
    SECURITY_AVAILABLE = True
except ImportError:
    try:
        # Fallback for direct execution
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from security import (
            User, UserRole, DatabasePermission, 
            UDS3SecurityManager, DatabaseAccessControl
        )
        SECURITY_AVAILABLE = True
    except ImportError:
        SECURITY_AVAILABLE = False
        logging.warning("Security module not available - running without access control")

logger = logging.getLogger(__name__)


class SecurityException(Exception):
    """Raised when security check fails"""
    pass


class SecureDatabaseAPI:
    """
    Security wrapper for database APIs
    
    Enforces:
    - User authentication required for all operations
    - Row-level security (users can only access their own data)
    - Permission checks before database operations
    - Automatic audit logging
    - Rate limiting per user
    """
    
    def __init__(
        self,
        underlying_api: Any,
        security_manager: Optional['UDS3SecurityManager'] = None,
        enable_rls: bool = True,
        enable_audit: bool = True
    ):
        """
        Initialize secure database API
        
        Args:
            underlying_api: The actual database API (PostgreSQL, Neo4j, etc.)
            security_manager: UDS3SecurityManager instance
            enable_rls: Enable row-level security
            enable_audit: Enable audit logging
        """
        self.api = underlying_api
        self.security = security_manager
        self.enable_rls = enable_rls
        self.enable_audit = enable_audit
        
        if not SECURITY_AVAILABLE:
            logger.warning("Security module not available - ALL OPERATIONS ALLOWED")
            self.enable_rls = False
            self.enable_audit = False
    
    # ========================================================================
    # CREATE Operations
    # ========================================================================
    
    def create(
        self,
        user: 'User',
        data: Dict[str, Any],
        resource_type: str = "document"
    ) -> Optional[str]:
        """
        Create new record with security checks
        
        Args:
            user: Authenticated user
            data: Record data
            resource_type: Type of resource being created
            
        Returns:
            Record ID if successful, None if access denied
            
        Raises:
            SecurityException: If access denied
        """
        # Check rate limit
        if self.security:
            allowed, error = self.security.check_rate_limit(user)
            if not allowed:
                raise SecurityException(f"Rate limit exceeded: {error}")
        
        # Check write permission
        if self.enable_rls and self.security:
            # For new records, user becomes the owner
            can_write = self.security.check_access(
                user=user,
                action="write",
                owner_user_id=user.user_id,
                resource_type=resource_type
            )
            
            if not can_write:
                raise SecurityException(
                    f"User {user.username} does not have permission to create {resource_type}"
                )
        
        # Inject owner metadata
        secured_data = data.copy()
        secured_data['_owner_user_id'] = user.user_id
        secured_data['_created_by'] = user.username
        secured_data['_created_at'] = datetime.now().isoformat()
        
        # Execute database operation
        try:
            result = self.api.create(secured_data)
            
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="create",
                    resource_type=resource_type,
                    resource_id=result,
                    success=True
                )
            
            return result
            
        except Exception as e:
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="create",
                    resource_type=resource_type,
                    resource_id=None,
                    success=False,
                    error=str(e)
                )
            raise
    
    # ========================================================================
    # READ Operations
    # ========================================================================
    
    def read(
        self,
        user: 'User',
        filters: Optional[Dict[str, Any]] = None,
        resource_type: str = "document"
    ) -> List[Dict[str, Any]]:
        """
        Read records with row-level security
        
        Args:
            user: Authenticated user
            filters: Query filters
            resource_type: Type of resource being read
            
        Returns:
            List of records user has access to
        """
        # Check rate limit
        if self.security:
            allowed, error = self.security.check_rate_limit(user)
            if not allowed:
                raise SecurityException(f"Rate limit exceeded: {error}")
        
        # Check read permission
        if not user.has_permission(DatabasePermission.DATA_READ_OWN) and \
           not user.has_permission(DatabasePermission.DATA_READ_ALL):
            raise SecurityException(
                f"User {user.username} does not have read permission"
            )
        
        # Apply row-level security filter
        secured_filters = filters.copy() if filters else {}
        
        if self.enable_rls:
            # Users can only see their own data (unless ADMIN/SYSTEM/SERVICE)
            if user.role not in {UserRole.SYSTEM, UserRole.ADMIN, UserRole.SERVICE}:
                secured_filters['_owner_user_id'] = user.user_id
        
        # Execute database operation
        try:
            results = self.api.read(secured_filters)
            
            # Additional RLS check in case database doesn't support it
            if self.enable_rls and results:
                filtered_results = []
                for record in results:
                    owner_id = record.get('_owner_user_id', user.user_id)
                    
                    if self.security:
                        can_read = self.security.check_access(
                            user=user,
                            action="read",
                            owner_user_id=owner_id,
                            resource_type=resource_type,
                            resource_id=record.get('id', 'unknown')
                        )
                        if can_read:
                            filtered_results.append(record)
                    else:
                        # No security manager - allow if own data
                        if owner_id == user.user_id or user.role in {UserRole.SYSTEM, UserRole.ADMIN}:
                            filtered_results.append(record)
                
                results = filtered_results
            
            return results
            
        except Exception as e:
            logger.error(f"Read operation failed: {e}")
            raise
    
    def read_by_id(
        self,
        user: 'User',
        record_id: str,
        resource_type: str = "document"
    ) -> Optional[Dict[str, Any]]:
        """
        Read single record by ID with security check
        
        Args:
            user: Authenticated user
            record_id: Record identifier
            resource_type: Type of resource
            
        Returns:
            Record if found and accessible, None otherwise
        """
        # Check rate limit
        if self.security:
            allowed, error = self.security.check_rate_limit(user)
            if not allowed:
                raise SecurityException(f"Rate limit exceeded: {error}")
        
        # Fetch record
        try:
            record = self.api.read_by_id(record_id)
            
            if not record:
                return None
            
            # Check access
            owner_id = record.get('_owner_user_id', user.user_id)
            
            if self.enable_rls and self.security:
                can_read = self.security.check_access(
                    user=user,
                    action="read",
                    owner_user_id=owner_id,
                    resource_type=resource_type,
                    resource_id=record_id
                )
                
                if not can_read:
                    logger.warning(
                        f"Access denied: {user.username} attempted to read "
                        f"{resource_type}/{record_id} owned by {owner_id}"
                    )
                    return None
            
            return record
            
        except Exception as e:
            logger.error(f"Read by ID operation failed: {e}")
            raise
    
    # ========================================================================
    # UPDATE Operations
    # ========================================================================
    
    def update(
        self,
        user: 'User',
        record_id: str,
        updates: Dict[str, Any],
        resource_type: str = "document"
    ) -> bool:
        """
        Update record with security checks
        
        Args:
            user: Authenticated user
            record_id: Record to update
            updates: Fields to update
            resource_type: Type of resource
            
        Returns:
            True if successful, False otherwise
        """
        # Check rate limit
        if self.security:
            allowed, error = self.security.check_rate_limit(user)
            if not allowed:
                raise SecurityException(f"Rate limit exceeded: {error}")
        
        # Fetch existing record to check ownership
        existing = self.api.read_by_id(record_id)
        if not existing:
            raise ValueError(f"Record {record_id} not found")
        
        owner_id = existing.get('_owner_user_id', user.user_id)
        
        # Check write permission
        if self.enable_rls and self.security:
            can_write = self.security.check_access(
                user=user,
                action="write",
                owner_user_id=owner_id,
                resource_type=resource_type,
                resource_id=record_id
            )
            
            if not can_write:
                raise SecurityException(
                    f"User {user.username} does not have permission to update "
                    f"{resource_type}/{record_id} owned by {owner_id}"
                )
        
        # Add update metadata
        secured_updates = updates.copy()
        secured_updates['_updated_by'] = user.username
        secured_updates['_updated_at'] = datetime.now().isoformat()
        
        # Prevent changing ownership (unless ADMIN)
        if '_owner_user_id' in secured_updates and user.role != UserRole.ADMIN:
            del secured_updates['_owner_user_id']
        
        # Execute update
        try:
            result = self.api.update(record_id, secured_updates)
            
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="update",
                    resource_type=resource_type,
                    resource_id=record_id,
                    success=True
                )
            
            return result
            
        except Exception as e:
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="update",
                    resource_type=resource_type,
                    resource_id=record_id,
                    success=False,
                    error=str(e)
                )
            raise
    
    # ========================================================================
    # DELETE Operations
    # ========================================================================
    
    def delete(
        self,
        user: 'User',
        record_id: str,
        resource_type: str = "document"
    ) -> bool:
        """
        Delete record with security checks
        
        Args:
            user: Authenticated user
            record_id: Record to delete
            resource_type: Type of resource
            
        Returns:
            True if successful, False otherwise
        """
        # Check rate limit
        if self.security:
            allowed, error = self.security.check_rate_limit(user)
            if not allowed:
                raise SecurityException(f"Rate limit exceeded: {error}")
        
        # Fetch existing record to check ownership
        existing = self.api.read_by_id(record_id)
        if not existing:
            raise ValueError(f"Record {record_id} not found")
        
        owner_id = existing.get('_owner_user_id', user.user_id)
        
        # Check delete permission
        if self.enable_rls and self.security:
            can_delete = self.security.check_access(
                user=user,
                action="delete",
                owner_user_id=owner_id,
                resource_type=resource_type,
                resource_id=record_id
            )
            
            if not can_delete:
                raise SecurityException(
                    f"User {user.username} does not have permission to delete "
                    f"{resource_type}/{record_id} owned by {owner_id}"
                )
        
        # Execute delete
        try:
            result = self.api.delete(record_id)
            
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="delete",
                    resource_type=resource_type,
                    resource_id=record_id,
                    success=True
                )
            
            return result
            
        except Exception as e:
            if self.enable_audit and self.security and self.security.access_control:
                self.security.access_control._log_access(
                    user=user,
                    action="delete",
                    resource_type=resource_type,
                    resource_id=record_id,
                    success=False,
                    error=str(e)
                )
            raise
    
    # ========================================================================
    # Batch Operations (with RLS)
    # ========================================================================
    
    def batch_create(
        self,
        user: 'User',
        records: List[Dict[str, Any]],
        resource_type: str = "document"
    ) -> List[str]:
        """Batch create with security checks"""
        # Check permission
        if not user.has_permission(DatabasePermission.BATCH_WRITE):
            raise SecurityException(
                f"User {user.username} does not have batch write permission"
            )
        
        # Inject owner metadata for all records
        secured_records = []
        for record in records:
            secured = record.copy()
            secured['_owner_user_id'] = user.user_id
            secured['_created_by'] = user.username
            secured['_created_at'] = datetime.now().isoformat()
            secured_records.append(secured)
        
        # Execute batch create
        return self.api.batch_create(secured_records)
    
    def batch_read(
        self,
        user: 'User',
        filters: Optional[Dict[str, Any]] = None,
        resource_type: str = "document"
    ) -> List[Dict[str, Any]]:
        """Batch read with RLS filtering"""
        # Check permission
        if not user.has_permission(DatabasePermission.BATCH_READ):
            raise SecurityException(
                f"User {user.username} does not have batch read permission"
            )
        
        # Apply RLS filter
        return self.read(user, filters, resource_type)
    
    # ========================================================================
    # Audit & Monitoring
    # ========================================================================
    
    def get_user_audit_log(
        self,
        admin_user: 'User',
        target_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log (admin only)
        
        Args:
            admin_user: Admin user requesting logs
            target_user_id: Optional user ID to filter logs
            
        Returns:
            List of audit log entries
        """
        if admin_user.role != UserRole.ADMIN:
            raise SecurityException("Only admins can access audit logs")
        
        if not self.security or not self.security.access_control:
            return []
        
        entries = self.security.access_control.get_audit_log(user_id=target_user_id)
        
        return [
            {
                'timestamp': e.timestamp.isoformat(),
                'user_id': e.user_id,
                'username': e.username,
                'role': e.role.value,
                'action': e.action,
                'resource_type': e.resource_type,
                'resource_id': e.resource_id,
                'success': e.success,
                'error': e.error_message
            }
            for e in entries
        ]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SECURE DATABASE API - DEMONSTRATION")
    print("="*70 + "\n")
    
    if not SECURITY_AVAILABLE:
        print("❌ Security module not available")
        exit(1)
    
    from security import User, UserRole, UDS3SecurityManager
    
    # Mock database API
    class MockDatabaseAPI:
        def __init__(self):
            self.storage = {}
        
        def create(self, data):
            record_id = f"rec_{len(self.storage)+1}"
            self.storage[record_id] = data
            return record_id
        
        def read(self, filters):
            results = []
            for rec_id, record in self.storage.items():
                match = all(record.get(k) == v for k, v in (filters or {}).items())
                if match:
                    result = record.copy()
                    result['id'] = rec_id
                    results.append(result)
            return results
        
        def read_by_id(self, record_id):
            record = self.storage.get(record_id)
            if record:
                result = record.copy()
                result['id'] = record_id
                return result
            return None
        
        def update(self, record_id, updates):
            if record_id in self.storage:
                self.storage[record_id].update(updates)
                return True
            return False
        
        def delete(self, record_id):
            if record_id in self.storage:
                del self.storage[record_id]
                return True
            return False
    
    # Setup
    mock_api = MockDatabaseAPI()
    security_manager = UDS3SecurityManager(
        enable_pki_auth=False,
        enable_rate_limiting=True,
        enable_audit_logging=True
    )
    secure_api = SecureDatabaseAPI(mock_api, security_manager)
    
    # Create users
    admin = User("admin001", "admin", "admin@vcc.local", UserRole.ADMIN)
    user1 = User("user001", "alice", "alice@vcc.local", UserRole.USER)
    user2 = User("user002", "bob", "bob@vcc.local", UserRole.USER)
    
    print("1. Creating Records")
    print("-" * 50)
    
    # Alice creates a document
    doc1_id = secure_api.create(user1, {"title": "Alice's Document", "content": "Secret data"})
    print(f"  ✅ Alice created: {doc1_id}")
    
    # Bob creates a document
    doc2_id = secure_api.create(user2, {"title": "Bob's Document", "content": "Other secret"})
    print(f"  ✅ Bob created: {doc2_id}")
    
    print("\n2. Row-Level Security Test")
    print("-" * 50)
    
    # Alice reads her own document
    alice_docs = secure_api.read(user1, {})
    print(f"  ✅ Alice sees {len(alice_docs)} document(s): {[d['title'] for d in alice_docs]}")
    
    # Bob reads his own document
    bob_docs = secure_api.read(user2, {})
    print(f"  ✅ Bob sees {len(bob_docs)} document(s): {[d['title'] for d in bob_docs]}")
    
    # Alice tries to read Bob's document by ID (should fail)
    try:
        bob_doc = secure_api.read_by_id(user1, doc2_id)
        if bob_doc is None:
            print(f"  ❌ Alice cannot access Bob's document (RLS working)")
        else:
            print(f"  ⚠️ Alice accessed Bob's document (RLS failed!)")
    except SecurityException as e:
        print(f"  ❌ Security Exception: {e}")
    
    # Admin reads all documents
    admin_docs = secure_api.read(admin, {})
    print(f"  ✅ Admin sees {len(admin_docs)} document(s): {[d['title'] for d in admin_docs]}")
    
    print("\n3. Update & Delete Tests")
    print("-" * 50)
    
    # Alice updates her document
    success = secure_api.update(user1, doc1_id, {"content": "Updated content"})
    print(f"  ✅ Alice updated her document: {success}")
    
    # Bob tries to update Alice's document (should fail)
    try:
        secure_api.update(user2, doc1_id, {"content": "Hacked!"})
        print(f"  ⚠️ Bob updated Alice's document (SECURITY BREACH!)")
    except SecurityException as e:
        print(f"  ❌ Bob blocked from updating Alice's document")
    
    print("\n4. Audit Log")
    print("-" * 50)
    
    audit_log = secure_api.get_user_audit_log(admin)
    print(f"  📋 Total audit entries: {len(audit_log)}")
    for entry in audit_log[-5:]:  # Show last 5
        status = "✅" if entry['success'] else "❌"
        print(f"    {status} {entry['username']} {entry['action']} {entry['resource_type']}/{entry['resource_id']}")
    
    print("\n" + "="*70)
    print("✅ Secure Database API Demo Complete")
    print("="*70 + "\n")
