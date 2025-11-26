# VCC-UDS3 PEFT/LoRA Manager
# Copyright 2024-2025 VCC Development Team
# SPDX-License-Identifier: Apache-2.0

"""
Parameter-Efficient Fine-Tuning (PEFT) Manager for VCC-UDS3 v2.0.0

Provides:
- LoRA adapter configuration and management
- Adapter versioning and storage
- PKI-based adapter signing and verification
- Zero-downtime adapter deployment
- Resource-efficient training (< 5% additional GPU RAM)

Aligned with Clara integration for continuous learning architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class AdapterStatus(Enum):
    """Adapter lifecycle status."""
    CREATED = "created"
    TRAINING = "training"
    VALIDATING = "validating"
    SIGNED = "signed"
    DEPLOYED = "deployed"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class LoRATarget(Enum):
    """Target modules for LoRA adaptation."""
    Q_PROJ = "q_proj"
    K_PROJ = "k_proj"
    V_PROJ = "v_proj"
    O_PROJ = "o_proj"
    GATE_PROJ = "gate_proj"
    UP_PROJ = "up_proj"
    DOWN_PROJ = "down_proj"
    ALL_LINEAR = "all_linear"


@dataclass
class LoRAConfig:
    """
    LoRA adapter configuration.
    
    Attributes:
        r: Rank of the LoRA decomposition (default: 16)
        alpha: Scaling factor (default: 32)
        dropout: Dropout probability (default: 0.05)
        target_modules: Modules to apply LoRA (default: q_proj, v_proj)
        bias: Bias handling ("none", "all", "lora_only")
        use_rslora: Use Rank-Stabilized LoRA
        task_type: Type of task (CAUSAL_LM, SEQ_CLS, etc.)
    """
    r: int = 16
    alpha: int = 32
    dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    bias: str = "none"
    use_rslora: bool = False
    task_type: str = "CAUSAL_LM"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "r": self.r,
            "alpha": self.alpha,
            "dropout": self.dropout,
            "target_modules": self.target_modules,
            "bias": self.bias,
            "use_rslora": self.use_rslora,
            "task_type": self.task_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoRAConfig":
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def german_legal_config(cls) -> "LoRAConfig":
        """
        Optimized configuration for German legal domain.
        
        Based on best practices for legal text understanding:
        - Higher rank for complex legal relationships
        - Extended target modules for better adaptation
        """
        return cls(
            r=32,  # Higher rank for complex legal texts
            alpha=64,
            dropout=0.1,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            bias="none",
            use_rslora=True,
            task_type="CAUSAL_LM",
        )


@dataclass
class TrainingConfig:
    """
    Training configuration for PEFT adapters.
    
    Aligned with v2.0.0 KPIs:
    - Training Time < 2h
    - Accuracy +2% on Golden Dataset
    - GPU RAM overhead < 5%
    """
    batch_size: int = 4
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    num_epochs: int = 3
    warmup_steps: int = 100
    max_steps: int = -1  # -1 for full epochs
    logging_steps: int = 10
    eval_steps: int = 50
    save_steps: int = 100
    max_seq_length: int = 2048
    gradient_checkpointing: bool = True
    mixed_precision: str = "bf16"  # bf16, fp16, or none
    optimizer: str = "adamw_torch"
    
    # Resource constraints (on-premise deployment)
    max_gpu_memory_gb: float = 40.0  # Single GPU limit
    enable_cpu_offload: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "warmup_steps": self.warmup_steps,
            "max_steps": self.max_steps,
            "logging_steps": self.logging_steps,
            "eval_steps": self.eval_steps,
            "save_steps": self.save_steps,
            "max_seq_length": self.max_seq_length,
            "gradient_checkpointing": self.gradient_checkpointing,
            "mixed_precision": self.mixed_precision,
            "optimizer": self.optimizer,
            "max_gpu_memory_gb": self.max_gpu_memory_gb,
            "enable_cpu_offload": self.enable_cpu_offload,
        }


@dataclass
class AdapterMetadata:
    """
    Metadata for a trained LoRA adapter.
    
    Includes version info, performance metrics, and signature for integrity.
    """
    adapter_id: str
    version: str
    base_model: str
    created_at: datetime
    status: AdapterStatus
    lora_config: LoRAConfig
    training_config: TrainingConfig
    
    # Performance metrics from Golden Dataset evaluation
    accuracy: float = 0.0
    f1_score: float = 0.0
    bleu_score: float = 0.0
    latency_ms: float = 0.0
    
    # PKI signature for integrity verification
    signature: Optional[bytes] = None
    signed_at: Optional[datetime] = None
    signed_by: Optional[str] = None  # PKI certificate subject
    
    # Training metadata
    training_samples: int = 0
    training_duration_s: float = 0.0
    feedback_source: str = ""  # Source of training data
    
    # Deployment info
    deployed_at: Optional[datetime] = None
    deployment_nodes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "adapter_id": self.adapter_id,
            "version": self.version,
            "base_model": self.base_model,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "lora_config": self.lora_config.to_dict(),
            "training_config": self.training_config.to_dict(),
            "accuracy": self.accuracy,
            "f1_score": self.f1_score,
            "bleu_score": self.bleu_score,
            "latency_ms": self.latency_ms,
            "signature": self.signature.hex() if self.signature else None,
            "signed_at": self.signed_at.isoformat() if self.signed_at else None,
            "signed_by": self.signed_by,
            "training_samples": self.training_samples,
            "training_duration_s": self.training_duration_s,
            "feedback_source": self.feedback_source,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deployment_nodes": self.deployment_nodes,
        }
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of adapter configuration and metrics."""
        data = {
            "adapter_id": self.adapter_id,
            "version": self.version,
            "base_model": self.base_model,
            "lora_config": self.lora_config.to_dict(),
            "accuracy": self.accuracy,
            "f1_score": self.f1_score,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class PEFTManager:
    """
    PEFT/LoRA Manager for VCC-UDS3 v2.0.0
    
    Manages the full lifecycle of LoRA adapters:
    - Creation and configuration
    - Training orchestration
    - Validation against Golden Dataset
    - PKI signing and verification
    - Zero-downtime deployment
    - Revocation and archival
    
    Integration points:
    - Clara: Training infrastructure
    - Veritas: Feedback capture
    - VCC-PKI: Adapter signing
    - CouchDB: Adapter storage
    """
    
    def __init__(
        self,
        storage_backend: Any = None,
        pki_service: Any = None,
        clara_client: Any = None,
    ):
        """
        Initialize PEFT Manager.
        
        Args:
            storage_backend: CouchDB adapter storage
            pki_service: VCC-PKI for signing
            clara_client: Clara training service client
        """
        self.storage = storage_backend
        self.pki = pki_service
        self.clara = clara_client
        self._adapters: Dict[str, AdapterMetadata] = {}
        self._revocation_list: List[str] = []
        self._deployed_adapter: Optional[str] = None
        
    async def create_adapter(
        self,
        adapter_id: str,
        base_model: str,
        lora_config: Optional[LoRAConfig] = None,
        training_config: Optional[TrainingConfig] = None,
    ) -> AdapterMetadata:
        """
        Create a new LoRA adapter configuration.
        
        Args:
            adapter_id: Unique identifier for the adapter
            base_model: Base model name (e.g., "llama-3-70b")
            lora_config: LoRA configuration (default: german_legal_config)
            training_config: Training configuration
            
        Returns:
            AdapterMetadata for the new adapter
        """
        if adapter_id in self._adapters:
            raise ValueError(f"Adapter {adapter_id} already exists")
        
        lora_config = lora_config or LoRAConfig.german_legal_config()
        training_config = training_config or TrainingConfig()
        
        # Generate version from timestamp
        version = datetime.utcnow().strftime("%Y%m%d.%H%M%S")
        
        metadata = AdapterMetadata(
            adapter_id=adapter_id,
            version=version,
            base_model=base_model,
            created_at=datetime.utcnow(),
            status=AdapterStatus.CREATED,
            lora_config=lora_config,
            training_config=training_config,
        )
        
        self._adapters[adapter_id] = metadata
        logger.info(f"Created adapter {adapter_id} v{version} for {base_model}")
        
        return metadata
    
    async def train_adapter(
        self,
        adapter_id: str,
        training_data: List[Dict[str, Any]],
    ) -> AdapterMetadata:
        """
        Train a LoRA adapter with provided data.
        
        Aligned with v2.0.0 KPIs:
        - Training Time < 2h
        - GPU RAM overhead < 5%
        
        Args:
            adapter_id: Adapter to train
            training_data: List of training samples
            
        Returns:
            Updated AdapterMetadata with training results
        """
        if adapter_id not in self._adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        metadata = self._adapters[adapter_id]
        metadata.status = AdapterStatus.TRAINING
        metadata.training_samples = len(training_data)
        
        start_time = datetime.utcnow()
        logger.info(f"Starting training for {adapter_id} with {len(training_data)} samples")
        
        try:
            # Simulate training (actual implementation would use Clara)
            if self.clara:
                result = await self.clara.train_lora_adapter(
                    adapter_id=adapter_id,
                    base_model=metadata.base_model,
                    lora_config=metadata.lora_config.to_dict(),
                    training_config=metadata.training_config.to_dict(),
                    training_data=training_data,
                )
                metadata.accuracy = result.get("accuracy", 0.0)
                metadata.f1_score = result.get("f1_score", 0.0)
            else:
                # Fallback for testing without Clara
                logger.warning("Clara not available, using mock training")
                metadata.accuracy = 0.85
                metadata.f1_score = 0.82
            
            end_time = datetime.utcnow()
            metadata.training_duration_s = (end_time - start_time).total_seconds()
            metadata.status = AdapterStatus.VALIDATING
            
            logger.info(
                f"Training completed for {adapter_id}: "
                f"accuracy={metadata.accuracy:.3f}, "
                f"duration={metadata.training_duration_s:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Training failed for {adapter_id}: {e}")
            metadata.status = AdapterStatus.CREATED
            raise
        
        return metadata
    
    async def sign_adapter(
        self,
        adapter_id: str,
        adapter_bytes: bytes,
    ) -> AdapterMetadata:
        """
        Sign a trained adapter with PKI.
        
        v2.0.0 Security requirement:
        - Digital signature of all LoRA adapters
        - Verification overhead < 10ms
        - Zero false positives
        
        Args:
            adapter_id: Adapter to sign
            adapter_bytes: Serialized adapter weights
            
        Returns:
            Updated AdapterMetadata with signature
        """
        if adapter_id not in self._adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        metadata = self._adapters[adapter_id]
        
        if self.pki:
            signature = await self.pki.sign(adapter_bytes)
            signed_by = await self.pki.get_certificate_subject()
        else:
            # Fallback: compute hash as mock signature
            logger.warning("PKI not available, using hash as mock signature")
            signature = hashlib.sha256(adapter_bytes).digest()
            signed_by = "mock-signer"
        
        metadata.signature = signature
        metadata.signed_at = datetime.utcnow()
        metadata.signed_by = signed_by
        metadata.status = AdapterStatus.SIGNED
        
        logger.info(f"Signed adapter {adapter_id} by {signed_by}")
        
        return metadata
    
    async def verify_adapter(
        self,
        adapter_id: str,
        adapter_bytes: bytes,
    ) -> Tuple[bool, str]:
        """
        Verify adapter signature before deployment.
        
        v2.0.0 Security requirement:
        - Runtime verification before GPU loading
        - Revocation list check
        - Verification overhead < 10ms
        
        Args:
            adapter_id: Adapter to verify
            adapter_bytes: Serialized adapter weights
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if adapter_id not in self._adapters:
            return False, f"Adapter {adapter_id} not found"
        
        # Check revocation list
        if adapter_id in self._revocation_list:
            return False, f"Adapter {adapter_id} is revoked"
        
        metadata = self._adapters[adapter_id]
        
        if not metadata.signature:
            return False, f"Adapter {adapter_id} is not signed"
        
        if self.pki:
            is_valid = await self.pki.verify(adapter_bytes, metadata.signature)
        else:
            # Fallback: verify hash
            expected = hashlib.sha256(adapter_bytes).digest()
            is_valid = metadata.signature == expected
        
        if is_valid:
            return True, "Signature verified successfully"
        else:
            return False, "Signature verification failed"
    
    async def deploy_adapter(
        self,
        adapter_id: str,
        target_nodes: Optional[List[str]] = None,
    ) -> AdapterMetadata:
        """
        Deploy a signed adapter with zero downtime.
        
        Args:
            adapter_id: Adapter to deploy
            target_nodes: Deployment target nodes (default: all)
            
        Returns:
            Updated AdapterMetadata
        """
        if adapter_id not in self._adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        metadata = self._adapters[adapter_id]
        
        if metadata.status != AdapterStatus.SIGNED:
            raise ValueError(f"Adapter {adapter_id} must be signed before deployment")
        
        target_nodes = target_nodes or ["inference-node-1"]
        
        # Swap adapters atomically
        previous_adapter = self._deployed_adapter
        self._deployed_adapter = adapter_id
        
        metadata.deployed_at = datetime.utcnow()
        metadata.deployment_nodes = target_nodes
        metadata.status = AdapterStatus.DEPLOYED
        
        logger.info(
            f"Deployed adapter {adapter_id} to {target_nodes} "
            f"(replaced {previous_adapter})"
        )
        
        return metadata
    
    async def revoke_adapter(self, adapter_id: str, reason: str) -> None:
        """
        Revoke a compromised or faulty adapter.
        
        Args:
            adapter_id: Adapter to revoke
            reason: Revocation reason for audit log
        """
        if adapter_id not in self._adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        self._revocation_list.append(adapter_id)
        metadata = self._adapters[adapter_id]
        metadata.status = AdapterStatus.REVOKED
        
        # If this was the deployed adapter, remove from service
        if self._deployed_adapter == adapter_id:
            self._deployed_adapter = None
            logger.warning(f"Revoked deployed adapter {adapter_id}, service running without adapter")
        
        logger.warning(f"Revoked adapter {adapter_id}: {reason}")
    
    def get_adapter(self, adapter_id: str) -> Optional[AdapterMetadata]:
        """Get adapter metadata by ID."""
        return self._adapters.get(adapter_id)
    
    def get_deployed_adapter(self) -> Optional[AdapterMetadata]:
        """Get currently deployed adapter."""
        if self._deployed_adapter:
            return self._adapters.get(self._deployed_adapter)
        return None
    
    def list_adapters(
        self,
        status: Optional[AdapterStatus] = None,
    ) -> List[AdapterMetadata]:
        """List all adapters, optionally filtered by status."""
        adapters = list(self._adapters.values())
        if status:
            adapters = [a for a in adapters if a.status == status]
        return adapters
