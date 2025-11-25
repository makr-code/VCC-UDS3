# VCC-UDS3 Feedback Loop
# Copyright 2024-2025 VCC Development Team
# SPDX-License-Identifier: Apache-2.0

"""
Feedback Loop for VCC-UDS3 v2.0.0

Provides:
- Veritas → Clara feedback pipeline
- Anonymized data processing (DSGVO compliant)
- Human-in-the-loop expert review
- Training data quality validation

Aligned with v2.0.0 requirements:
- Feedback capture from Veritas UI
- Pseudonymization and Opt-Out
- Expert review for critical cases
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Type of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    COMMENT = "comment"
    CORRECTION = "correction"
    EXPERT_REVIEW = "expert_review"


class PipelineStatus(Enum):
    """Feedback pipeline status."""
    RECEIVED = "received"
    ANONYMIZED = "anonymized"
    QUALITY_CHECKED = "quality_checked"
    EXPERT_REVIEW = "expert_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    TRAINING_READY = "training_ready"
    USED_FOR_TRAINING = "used_for_training"


@dataclass
class FeedbackItem:
    """
    A single feedback item from Veritas.
    
    Contains user feedback with DSGVO-compliant anonymization.
    """
    feedback_id: str
    feedback_type: FeedbackType
    created_at: datetime
    status: PipelineStatus
    
    # Original query and response
    query: str
    response: str
    
    # User feedback
    is_helpful: Optional[bool] = None
    user_comment: str = ""
    user_correction: str = ""
    
    # Source references
    source_document_ids: List[str] = field(default_factory=list)
    
    # Anonymization (DSGVO)
    user_id_hash: str = ""  # Pseudonymized user ID
    opt_out: bool = False  # User opted out of training
    anonymized_at: Optional[datetime] = None
    
    # Quality validation
    quality_score: float = 0.0
    quality_issues: List[str] = field(default_factory=list)
    validated_at: Optional[datetime] = None
    
    # Expert review (critical cases)
    requires_expert_review: bool = False
    expert_reviewer: str = ""
    expert_decision: str = ""
    expert_reviewed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.value,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "query": self.query,
            "response": self.response,
            "is_helpful": self.is_helpful,
            "user_comment": self.user_comment,
            "user_correction": self.user_correction,
            "source_document_ids": self.source_document_ids,
            "user_id_hash": self.user_id_hash,
            "opt_out": self.opt_out,
            "anonymized_at": self.anonymized_at.isoformat() if self.anonymized_at else None,
            "quality_score": self.quality_score,
            "quality_issues": self.quality_issues,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "requires_expert_review": self.requires_expert_review,
            "expert_reviewer": self.expert_reviewer,
            "expert_decision": self.expert_decision,
            "expert_reviewed_at": self.expert_reviewed_at.isoformat() if self.expert_reviewed_at else None,
        }


@dataclass
class FeedbackFilter:
    """Filter criteria for feedback queries."""
    feedback_types: Optional[List[FeedbackType]] = None
    status: Optional[List[PipelineStatus]] = None
    is_helpful: Optional[bool] = None
    requires_expert_review: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_quality_score: Optional[float] = None
    
    def matches(self, item: FeedbackItem) -> bool:
        """Check if feedback item matches filter."""
        if self.feedback_types and item.feedback_type not in self.feedback_types:
            return False
        if self.status and item.status not in self.status:
            return False
        if self.is_helpful is not None and item.is_helpful != self.is_helpful:
            return False
        if self.requires_expert_review is not None and item.requires_expert_review != self.requires_expert_review:
            return False
        if self.created_after and item.created_at < self.created_after:
            return False
        if self.created_before and item.created_at > self.created_before:
            return False
        if self.min_quality_score is not None and item.quality_score < self.min_quality_score:
            return False
        return True


class FeedbackLoop:
    """
    Feedback Loop Manager for VCC-UDS3 v2.0.0
    
    Manages the Veritas → Clara feedback pipeline:
    - Capture feedback from Veritas UI
    - Anonymize data (DSGVO compliant)
    - Validate data quality (Covina)
    - Route critical cases to expert review
    - Prepare training data for Clara
    
    Integration points:
    - Veritas: Feedback capture UI
    - Covina: Data quality validation
    - Clara: Training data consumption
    - PostgreSQL: Feedback storage
    """
    
    MIN_QUALITY_SCORE = 0.7  # Minimum quality for training
    
    def __init__(
        self,
        storage_backend: Any = None,
        covina_client: Any = None,
    ):
        """
        Initialize Feedback Loop.
        
        Args:
            storage_backend: PostgreSQL storage
            covina_client: Covina quality validation service
        """
        self.storage = storage_backend
        self.covina = covina_client
        self._feedback_items: Dict[str, FeedbackItem] = {}
        self._training_queue: List[str] = []
        
    async def capture_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        user_id: str,
        is_helpful: Optional[bool] = None,
        comment: str = "",
        correction: str = "",
        source_ids: Optional[List[str]] = None,
        opt_out: bool = False,
    ) -> FeedbackItem:
        """
        Capture feedback from Veritas UI.
        
        DSGVO compliant: User ID is immediately pseudonymized.
        
        Args:
            query: Original user query
            response: System response
            feedback_type: Type of feedback
            user_id: User identifier (will be hashed)
            is_helpful: Whether response was helpful
            comment: User's textual feedback
            correction: User's correction to response
            source_ids: Referenced document IDs
            opt_out: User opts out of training data usage
            
        Returns:
            Created FeedbackItem
        """
        # Generate feedback ID
        feedback_id = f"fb-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        # Pseudonymize user ID (DSGVO)
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        item = FeedbackItem(
            feedback_id=feedback_id,
            feedback_type=feedback_type,
            created_at=datetime.utcnow(),
            status=PipelineStatus.RECEIVED,
            query=query,
            response=response,
            is_helpful=is_helpful,
            user_comment=comment,
            user_correction=correction,
            source_document_ids=source_ids or [],
            user_id_hash=user_id_hash,
            opt_out=opt_out,
        )
        
        self._feedback_items[feedback_id] = item
        logger.info(f"Captured feedback {feedback_id} ({feedback_type.value})")
        
        # Immediately process through pipeline
        await self._process_feedback(item)
        
        return item
    
    async def _process_feedback(self, item: FeedbackItem) -> None:
        """Process feedback through the pipeline."""
        
        # Skip if user opted out
        if item.opt_out:
            item.status = PipelineStatus.REJECTED
            logger.info(f"Feedback {item.feedback_id} rejected (user opt-out)")
            return
        
        # Step 1: Anonymize
        item = await self._anonymize_feedback(item)
        
        # Step 2: Quality check
        item = await self._validate_quality(item)
        
        # Step 3: Route based on quality
        if item.requires_expert_review:
            item.status = PipelineStatus.EXPERT_REVIEW
            logger.info(f"Feedback {item.feedback_id} routed to expert review")
        elif item.quality_score >= self.MIN_QUALITY_SCORE:
            item.status = PipelineStatus.TRAINING_READY
            self._training_queue.append(item.feedback_id)
            logger.info(f"Feedback {item.feedback_id} ready for training")
        else:
            item.status = PipelineStatus.REJECTED
            logger.info(f"Feedback {item.feedback_id} rejected (quality: {item.quality_score:.2f})")
    
    async def _anonymize_feedback(self, item: FeedbackItem) -> FeedbackItem:
        """
        Anonymize feedback data (DSGVO compliant).
        
        - Remove PII from comments
        - Pseudonymize references
        - Mark anonymization timestamp
        """
        # Simple PII removal (actual implementation would use NER)
        anonymized_comment = item.user_comment
        anonymized_correction = item.user_correction
        
        # Remove common PII patterns (simplified)
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
        
        anonymized_comment = re.sub(email_pattern, '[EMAIL]', anonymized_comment)
        anonymized_comment = re.sub(phone_pattern, '[PHONE]', anonymized_comment)
        anonymized_correction = re.sub(email_pattern, '[EMAIL]', anonymized_correction)
        anonymized_correction = re.sub(phone_pattern, '[PHONE]', anonymized_correction)
        
        item.user_comment = anonymized_comment
        item.user_correction = anonymized_correction
        item.anonymized_at = datetime.utcnow()
        item.status = PipelineStatus.ANONYMIZED
        
        return item
    
    async def _validate_quality(self, item: FeedbackItem) -> FeedbackItem:
        """
        Validate feedback quality using Covina.
        
        Checks:
        - Content relevance
        - Legal domain alignment
        - Correction coherence
        - PII leakage
        """
        quality_issues = []
        quality_score = 1.0
        
        # Check minimum content length
        if len(item.query) < 10:
            quality_issues.append("Query too short")
            quality_score -= 0.3
        
        if len(item.response) < 20:
            quality_issues.append("Response too short")
            quality_score -= 0.2
        
        # Check for corrections without content
        if item.feedback_type == FeedbackType.CORRECTION and not item.user_correction:
            quality_issues.append("Correction feedback without correction text")
            quality_score -= 0.4
        
        # Critical cases require expert review
        critical_keywords = ["falsch", "fehler", "inkorrekt", "wrong", "incorrect"]
        if any(kw in item.user_comment.lower() for kw in critical_keywords):
            item.requires_expert_review = True
        
        # Use Covina for advanced validation if available
        if self.covina:
            try:
                covina_result = await self.covina.validate_feedback(
                    query=item.query,
                    response=item.response,
                    correction=item.user_correction,
                )
                quality_score = min(quality_score, covina_result.get("quality_score", quality_score))
                quality_issues.extend(covina_result.get("issues", []))
            except Exception as e:
                logger.warning(f"Covina validation failed: {e}")
        
        item.quality_score = max(0.0, min(1.0, quality_score))
        item.quality_issues = quality_issues
        item.validated_at = datetime.utcnow()
        item.status = PipelineStatus.QUALITY_CHECKED
        
        return item
    
    async def submit_expert_review(
        self,
        feedback_id: str,
        reviewer: str,
        decision: str,
        approved: bool,
    ) -> FeedbackItem:
        """
        Submit expert review decision.
        
        Args:
            feedback_id: Feedback to review
            reviewer: Expert reviewer ID
            decision: Review decision/notes
            approved: Whether approved for training
            
        Returns:
            Updated FeedbackItem
        """
        if feedback_id not in self._feedback_items:
            raise ValueError(f"Feedback {feedback_id} not found")
        
        item = self._feedback_items[feedback_id]
        
        item.expert_reviewer = reviewer
        item.expert_decision = decision
        item.expert_reviewed_at = datetime.utcnow()
        
        if approved:
            item.status = PipelineStatus.APPROVED
            self._training_queue.append(feedback_id)
            logger.info(f"Expert approved feedback {feedback_id} for training")
        else:
            item.status = PipelineStatus.REJECTED
            logger.info(f"Expert rejected feedback {feedback_id}: {decision}")
        
        return item
    
    def get_training_data(
        self,
        limit: Optional[int] = None,
        mark_as_used: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get training-ready feedback data for Clara.
        
        Args:
            limit: Maximum number of items
            mark_as_used: Mark items as used for training
            
        Returns:
            List of training data dictionaries
        """
        training_data = []
        
        for feedback_id in self._training_queue[:limit]:
            item = self._feedback_items.get(feedback_id)
            if not item:
                continue
            
            # Format for training
            training_sample = {
                "feedback_id": item.feedback_id,
                "query": item.query,
                "response": item.response,
                "correction": item.user_correction if item.user_correction else None,
                "is_positive": item.is_helpful or (item.feedback_type == FeedbackType.THUMBS_UP),
                "quality_score": item.quality_score,
            }
            training_data.append(training_sample)
            
            if mark_as_used:
                item.status = PipelineStatus.USED_FOR_TRAINING
        
        if mark_as_used and limit:
            self._training_queue = self._training_queue[limit:]
        elif mark_as_used:
            self._training_queue.clear()
        
        return training_data
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackItem]:
        """Get feedback item by ID."""
        return self._feedback_items.get(feedback_id)
    
    def list_feedback(
        self,
        filter_criteria: Optional[FeedbackFilter] = None,
        limit: Optional[int] = None,
    ) -> List[FeedbackItem]:
        """List feedback items with optional filtering."""
        items = list(self._feedback_items.values())
        
        if filter_criteria:
            items = [i for i in items if filter_criteria.matches(i)]
        
        # Sort by creation date descending
        items.sort(key=lambda x: x.created_at, reverse=True)
        
        if limit:
            items = items[:limit]
        
        return items
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback pipeline statistics."""
        items = list(self._feedback_items.values())
        
        status_counts = {}
        type_counts = {}
        
        for item in items:
            status_counts[item.status.value] = status_counts.get(item.status.value, 0) + 1
            type_counts[item.feedback_type.value] = type_counts.get(item.feedback_type.value, 0) + 1
        
        helpful_items = [i for i in items if i.is_helpful is True]
        unhelpful_items = [i for i in items if i.is_helpful is False]
        
        return {
            "total_feedback": len(items),
            "training_queue_size": len(self._training_queue),
            "by_status": status_counts,
            "by_type": type_counts,
            "helpful_count": len(helpful_items),
            "unhelpful_count": len(unhelpful_items),
            "helpful_rate": len(helpful_items) / len(items) if items else 0,
            "avg_quality_score": sum(i.quality_score for i in items) / len(items) if items else 0,
            "expert_review_pending": len([i for i in items if i.status == PipelineStatus.EXPERT_REVIEW]),
        }
