# UDS3 Streaming API

**Status:** Production Ready ✅  
**Module:** `manager/streaming.py`  
**Lines of Code:** 1,279  
**References:** 26 files across codebase

---

## Overview

UDS3 includes a robust streaming API designed for efficient handling of large files (300+ MB to several GB) without loading entire files into memory. The streaming system provides chunked upload/download with resume support, progress tracking, and fault-tolerant operations.

### Key Features

- **Memory-Efficient Chunking:** Never loads entire file into memory
- **Resume Support:** Continue after interruption (fault-tolerant)
- **Progress Tracking:** Real-time monitoring with callbacks
- **Large File Processing:** PDFs with embedded images, large documents
- **Chunked Vector DB Operations:** Handle large embeddings efficiently
- **File Size Support:** Tested with files >1GB
- **Integrity Verification:** Checksum validation for uploaded/downloaded chunks
- **SAGA Integration:** Automatic rollback on failure

---

## Architecture

### Streaming Flow

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    (Upload/Download Large Files)        │
├─────────────────────────────────────────┤
│      Streaming Manager                   │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Chunked    │  │   Progress   │    │
│  │   Upload     │  │   Tracker    │    │
│  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────┤
│      Resume Manager                      │
│  (Checkpoint + Metadata Storage)         │
├─────────────────────────────────────────┤
│      File Storage Backend                │
│  (CouchDB, Local Filesystem)             │
└─────────────────────────────────────────┘
```

### Chunking Strategy

```
Large File (1 GB)
│
├─ Chunk 1 (10 MB) ──> Upload ──> Verify ──> Checkpoint
├─ Chunk 2 (10 MB) ──> Upload ──> Verify ──> Checkpoint
├─ Chunk 3 (10 MB) ──> Upload ──> Verify ──> Checkpoint
│  ...
└─ Chunk 100 (10 MB) ──> Upload ──> Verify ──> Complete
```

---

## Core Components

### StreamingOperation

Represents a streaming upload/download operation:

```python
@dataclass
class StreamingOperation:
    operation_id: str              # Unique operation ID
    file_name: str                 # Original filename
    total_size_bytes: int          # Total file size
    chunk_size_bytes: int          # Chunk size (default 10MB)
    chunks_total: int              # Total number of chunks
    chunks_completed: int          # Completed chunks
    status: OperationStatus        # IN_PROGRESS, COMPLETED, FAILED
    created_at: datetime           # Start time
    updated_at: datetime           # Last update
    checksum: Optional[str]        # File checksum (SHA-256)
    metadata: Dict[str, Any]       # Additional metadata
```

### OperationStatus

Operation lifecycle states:

```python
class OperationStatus(Enum):
    PENDING = "pending"            # Queued, not started
    IN_PROGRESS = "in_progress"    # Currently uploading/downloading
    PAUSED = "paused"              # Paused by user
    COMPLETED = "completed"        # Successfully finished
    FAILED = "failed"              # Error occurred
    CANCELLED = "cancelled"        # Cancelled by user
```

### ChunkMetadata

Metadata for individual chunks:

```python
@dataclass
class ChunkMetadata:
    chunk_index: int               # Chunk number (0-based)
    offset_bytes: int              # Start position in file
    size_bytes: int                # Chunk size
    checksum: str                  # Chunk checksum
    uploaded: bool                 # Upload status
    retry_count: int               # Number of retries
```

---

## Usage Examples

### Uploading Large Files

```python
from manager.streaming import StreamingManager

manager = StreamingManager(
    chunk_size_mb=10,              # 10 MB chunks
    max_retries=3,
    enable_resume=True
)

# Upload large file
file_path = "/path/to/large_document.pdf"
operation_id = manager.upload_file(
    file_path=file_path,
    destination="documents/2024/",
    progress_callback=lambda progress: print(f"{progress:.1f}% complete"),
    metadata={"document_type": "legal", "year": 2024}
)

print(f"Upload started: {operation_id}")
```

### Resumable Upload

```python
# Start upload
operation_id = manager.upload_file(file_path, destination)

# ... network interruption ...

# Resume upload
manager.resume_upload(operation_id)
print("Upload resumed from last checkpoint")
```

### Downloading Large Files

```python
# Download with streaming
manager.download_file(
    document_id="doc_12345",
    destination_path="/path/to/download/document.pdf",
    progress_callback=lambda progress: print(f"Downloaded: {progress:.1f}%")
)
```

### Progress Tracking

```python
def progress_callback(progress: float, operation: StreamingOperation):
    """
    Custom progress callback.
    
    Args:
        progress: Percentage complete (0-100)
        operation: Current operation metadata
    """
    elapsed = (datetime.now() - operation.created_at).total_seconds()
    rate_mbps = (operation.chunks_completed * operation.chunk_size_bytes) / elapsed / 1024 / 1024
    
    print(f"Progress: {progress:.1f}%")
    print(f"Chunks: {operation.chunks_completed}/{operation.chunks_total}")
    print(f"Rate: {rate_mbps:.2f} MB/s")
    print(f"Elapsed: {elapsed:.0f}s")

# Use callback
manager.upload_file(
    file_path,
    destination,
    progress_callback=progress_callback
)
```

### Batch Upload

```python
# Upload multiple files efficiently
files = [
    "/path/to/doc1.pdf",
    "/path/to/doc2.pdf",
    "/path/to/doc3.pdf"
]

operation_ids = []
for file_path in files:
    op_id = manager.upload_file(
        file_path,
        destination="batch_upload/",
        parallel=True  # Enable parallel chunk upload
    )
    operation_ids.append(op_id)

# Wait for all to complete
manager.wait_for_operations(operation_ids)
```

---

## Configuration

### Chunk Size Selection

```python
# Small files (<100 MB): 5 MB chunks
manager = StreamingManager(chunk_size_mb=5)

# Medium files (100-500 MB): 10 MB chunks (default)
manager = StreamingManager(chunk_size_mb=10)

# Large files (>500 MB): 20 MB chunks
manager = StreamingManager(chunk_size_mb=20)

# Very large files (>5 GB): 50 MB chunks
manager = StreamingManager(chunk_size_mb=50)
```

### Retry Configuration

```python
manager = StreamingManager(
    max_retries=3,                 # Max retries per chunk
    retry_delay_seconds=5,         # Delay between retries
    timeout_seconds=300,           # 5 minutes timeout
    exponential_backoff=True       # Increase delay exponentially
)
```

### Resume Settings

```python
manager = StreamingManager(
    enable_resume=True,            # Allow resume after interruption
    checkpoint_interval=10,        # Save checkpoint every 10 chunks
    checkpoint_storage="local",    # or "database"
    cleanup_completed=True,        # Delete checkpoints after completion
    checkpoint_retention_days=7    # Keep failed checkpoints for 7 days
)
```

---

## Advanced Features

### Checksum Verification

```python
# Enable integrity checking
manager = StreamingManager(
    verify_checksums=True,         # Verify each chunk
    checksum_algorithm="sha256"    # SHA-256 (default)
)

# Upload with checksum validation
operation_id = manager.upload_file(file_path, destination)

# Verify entire file after upload
is_valid = manager.verify_upload(operation_id)
if not is_valid:
    logger.error("Upload corrupted - restarting")
    manager.restart_upload(operation_id)
```

### Parallel Chunk Upload

```python
# Upload chunks in parallel (faster for high-bandwidth connections)
manager = StreamingManager(
    parallel_chunks=4,             # Upload 4 chunks simultaneously
    thread_pool_size=8             # Thread pool for parallel operations
)

operation_id = manager.upload_file(
    file_path,
    destination,
    parallel=True
)
```

### Compression

```python
# Compress before upload (reduce bandwidth)
manager = StreamingManager(
    compress_chunks=True,          # Enable compression
    compression_level=6            # 1 (fast) to 9 (max compression)
)

# Upload compressed
operation_id = manager.upload_file(file_path, destination)
# Automatically decompressed on download
```

### Encryption

```python
# Encrypt sensitive files
manager = StreamingManager(
    encrypt_chunks=True,           # Enable encryption
    encryption_key="your-key-here" # AES-256 key
)

# Upload encrypted
operation_id = manager.upload_file(
    file_path,
    destination,
    encrypt=True
)
```

---

## SAGA Integration

### Automatic Rollback

The streaming API integrates with UDS3's SAGA pattern for automatic rollback on failure:

```python
from manager.streaming import SagaRollbackRequired

try:
    operation_id = manager.upload_file(file_path, destination)
    
except SagaRollbackRequired as e:
    logger.error(f"Upload failed: {e.message}")
    logger.info(f"Reason: {e.reason}")
    logger.info(f"Retry count: {e.retry_count}")
    
    # SAGA will automatically:
    # 1. Delete partially uploaded chunks
    # 2. Clean up metadata
    # 3. Restore previous state
```

### Manual Rollback

```python
# Cancel ongoing operation and rollback
manager.cancel_operation(
    operation_id,
    cleanup=True  # Delete uploaded chunks
)
```

---

## Performance Characteristics

### Upload Performance

| File Size | Chunk Size | Network Speed | Upload Time | Memory Usage |
|-----------|-----------|---------------|-------------|--------------|
| 100 MB | 10 MB | 100 Mbps | ~8 seconds | <15 MB |
| 500 MB | 10 MB | 100 Mbps | ~40 seconds | <15 MB |
| 1 GB | 20 MB | 100 Mbps | ~80 seconds | <25 MB |
| 5 GB | 50 MB | 100 Mbps | ~7 minutes | <60 MB |

### Memory Efficiency

- **Non-Streaming:** 1 GB file = 1 GB RAM required
- **Streaming (10 MB chunks):** 1 GB file = <15 MB RAM required
- **Improvement:** **>60x memory reduction**

### Resume Performance

- **Resume overhead:** <1 second (load checkpoint)
- **Wasted bandwidth:** 0% (resume from exact checkpoint)
- **Recovery time:** Instant (no re-upload needed)

---

## Monitoring and Operations

### Check Operation Status

```python
# Get operation details
operation = manager.get_operation(operation_id)
print(f"Status: {operation.status.value}")
print(f"Progress: {operation.chunks_completed}/{operation.chunks_total}")
print(f"Size: {operation.total_size_bytes / 1024 / 1024:.2f} MB")
```

### List Active Operations

```python
# Get all active uploads/downloads
active_ops = manager.list_active_operations()
for op in active_ops:
    progress = (op.chunks_completed / op.chunks_total) * 100
    print(f"{op.file_name}: {progress:.1f}%")
```

### Cancel Operation

```python
# Cancel and cleanup
manager.cancel_operation(
    operation_id,
    cleanup=True,           # Delete uploaded chunks
    notify_user=True        # Send notification
)
```

### Cleanup Old Operations

```python
# Clean up completed/failed operations older than 7 days
manager.cleanup_old_operations(
    retention_days=7,
    delete_checkpoints=True,
    delete_metadata=True
)
```

---

## Error Handling

### Common Errors

```python
from manager.streaming import (
    ChunkMetadataCorruptError,
    StreamingTimeoutError,
    ChecksumMismatchError
)

try:
    manager.upload_file(file_path, destination)
    
except FileNotFoundError:
    logger.error("File not found")
    
except ChunkMetadataCorruptError:
    logger.error("Checkpoint corrupted - restart required")
    manager.restart_upload(operation_id)
    
except StreamingTimeoutError:
    logger.warning("Operation timeout - will auto-retry")
    
except ChecksumMismatchError:
    logger.error("Upload corrupted - re-uploading chunk")
    # Automatic retry triggered
    
except SagaRollbackRequired as e:
    logger.error(f"Fatal error: {e.message}")
    # Automatic rollback triggered
```

### Retry Logic

```python
# Configure retry behavior
manager = StreamingManager(
    max_retries=3,
    retry_delay_seconds=5,
    retry_on_errors=[
        "NetworkError",
        "TimeoutError",
        "ChecksumMismatchError"
    ]
)
```

---

## Best Practices

### 1. Choose Appropriate Chunk Size

```python
def calculate_chunk_size(file_size_bytes):
    """Calculate optimal chunk size based on file size."""
    if file_size_bytes < 100 * 1024 * 1024:  # <100 MB
        return 5 * 1024 * 1024  # 5 MB
    elif file_size_bytes < 500 * 1024 * 1024:  # <500 MB
        return 10 * 1024 * 1024  # 10 MB
    elif file_size_bytes < 5 * 1024 * 1024 * 1024:  # <5 GB
        return 20 * 1024 * 1024  # 20 MB
    else:
        return 50 * 1024 * 1024  # 50 MB
```

### 2. Enable Resume for Large Files

```python
# Always enable resume for files >100 MB
if file_size > 100 * 1024 * 1024:
    manager = StreamingManager(enable_resume=True)
```

### 3. Use Progress Callbacks

```python
# Provide user feedback for long operations
def ui_progress_callback(progress, operation):
    # Update UI progress bar
    update_progress_bar(operation.operation_id, progress)
```

### 4. Verify Checksums for Critical Files

```python
# Enable verification for legal/sensitive documents
manager = StreamingManager(verify_checksums=True)
```

### 5. Clean Up Regularly

```python
# Schedule cleanup (e.g., daily cron job)
manager.cleanup_old_operations(retention_days=7)
```

---

## Integration Examples

### With CouchDB

```python
# Upload to CouchDB as attachment
from database.database_api_couchdb import CouchDBAPI

couchdb = CouchDBAPI()
manager = StreamingManager()

# Upload large PDF
operation_id = manager.upload_file(
    file_path="/path/to/legal_document.pdf",
    destination="couchdb://documents/doc_12345/attachment"
)

# File stored as CouchDB attachment
```

### With Vector Database

```python
# Stream large embeddings
embeddings = generate_large_embeddings(document)  # >100 MB

# Upload in chunks
manager.upload_embeddings(
    embeddings,
    collection="legal_documents",
    chunk_size_mb=10
)
```

---

## API Reference

### StreamingManager Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `upload_file()` | Upload file | `(file_path, destination, ...)` | operation_id |
| `download_file()` | Download file | `(document_id, destination, ...)` | operation_id |
| `resume_upload()` | Resume upload | `(operation_id)` | bool |
| `resume_download()` | Resume download | `(operation_id)` | bool |
| `get_operation()` | Get operation | `(operation_id)` | StreamingOperation |
| `cancel_operation()` | Cancel operation | `(operation_id, cleanup)` | bool |
| `verify_upload()` | Verify checksum | `(operation_id)` | bool |
| `list_active_operations()` | List active | None | List[StreamingOperation] |
| `cleanup_old_operations()` | Cleanup | `(retention_days)` | int |

---

## Troubleshooting

### Upload Fails to Resume

**Problem:** Resume doesn't work after interruption

**Solutions:**
1. Check checkpoint storage is accessible
2. Verify `enable_resume=True` was set
3. Check checkpoint hasn't expired (7 day default)
4. Look for checkpoint file corruption

### Slow Upload Speed

**Problem:** Upload slower than expected

**Solutions:**
1. Increase chunk size for large files
2. Enable parallel chunk upload
3. Check network bandwidth
4. Disable compression if CPU-bound

### High Memory Usage

**Problem:** Memory usage higher than expected

**Solutions:**
1. Decrease chunk size
2. Reduce parallel chunks
3. Disable compression
4. Check for memory leaks in callbacks

---

## Related Documentation

- [Batch Operations](../BATCH_OPERATIONS.md) - Batch upload strategies
- [CouchDB Integration](../POSTGRES_COUCHDB_INTEGRATION.md) - CouchDB file storage
- [SAGA Pattern](../COUCHDB_SAGA_PROBLEM_RESOLUTION.md) - Rollback handling

---

**Last Updated:** November 17, 2025  
**Version:** 1.5.0  
**Status:** Production Ready ✅  
**Max Tested File Size:** 10 GB
