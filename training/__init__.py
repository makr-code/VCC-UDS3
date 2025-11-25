# VCC-UDS3 Training Module
# Copyright 2024-2025 VCC Development Team
# SPDX-License-Identifier: Apache-2.0

"""
Training module for VCC-UDS3 v2.0.0
Provides PEFT/LoRA adapter management and training infrastructure.

Components:
- PEFTManager: PEFT/LoRA adapter management
- GoldenDataset: Expert-validated evaluation dataset
- FeedbackLoop: Veritas → Clara feedback pipeline
- AdapterSigner: PKI-based adapter integrity verification
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .peft_manager import (
        PEFTManager,
        LoRAConfig,
        AdapterMetadata,
        TrainingConfig,
    )
    from .golden_dataset import (
        GoldenDataset,
        GoldenSample,
        EvaluationResult,
        RegressionAlert,
    )
    from .feedback_loop import (
        FeedbackLoop,
        FeedbackItem,
        FeedbackFilter,
        PipelineStatus,
    )

__all__ = [
    # PEFT Manager
    "PEFTManager",
    "LoRAConfig",
    "AdapterMetadata",
    "TrainingConfig",
    # Golden Dataset
    "GoldenDataset",
    "GoldenSample",
    "EvaluationResult",
    "RegressionAlert",
    # Feedback Loop
    "FeedbackLoop",
    "FeedbackItem",
    "FeedbackFilter",
    "PipelineStatus",
]
