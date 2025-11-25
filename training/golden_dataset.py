# VCC-UDS3 Golden Dataset Manager
# Copyright 2024-2025 VCC Development Team
# SPDX-License-Identifier: Apache-2.0

"""
Golden Dataset Manager for VCC-UDS3 v2.0.0

Provides:
- Expert-validated evaluation dataset (1000+ QA pairs)
- Automated pre-deployment validation
- Regression detection with alerts
- Performance metrics computation

Aligned with v2.0.0 KPIs:
- Accuracy +2% improvement on Golden Dataset
- Regression alert on Accuracy drop > 5%
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Difficulty classification for Golden Dataset samples."""
    SIMPLE = "simple"  # Direct fact lookup
    MEDIUM = "medium"  # Multi-step reasoning
    COMPLEX = "complex"  # Multi-hop, cross-reference
    EXPERT = "expert"  # Edge cases, ambiguous


class LegalDomain(Enum):
    """Legal domain classification."""
    BAURECHT = "baurecht"
    VERWALTUNGSRECHT = "verwaltungsrecht"
    UMWELTRECHT = "umweltrecht"
    STEUERRECHT = "steuerrecht"
    SOZIALRECHT = "sozialrecht"
    ALLGEMEIN = "allgemein"


@dataclass
class GoldenSample:
    """
    A single sample from the Golden Dataset.
    
    Expert-validated question-answer pair with metadata.
    """
    sample_id: str
    question: str
    expected_answer: str
    domain: LegalDomain
    difficulty: DifficultyLevel
    
    # Source references (§ references, document IDs)
    source_references: List[str] = field(default_factory=list)
    
    # Expert validation
    validated_by: str = ""
    validated_at: Optional[datetime] = None
    validation_notes: str = ""
    
    # Alternative acceptable answers
    alternative_answers: List[str] = field(default_factory=list)
    
    # Keywords for partial matching
    required_keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sample_id": self.sample_id,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "domain": self.domain.value,
            "difficulty": self.difficulty.value,
            "source_references": self.source_references,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "validation_notes": self.validation_notes,
            "alternative_answers": self.alternative_answers,
            "required_keywords": self.required_keywords,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoldenSample":
        """Create from dictionary."""
        return cls(
            sample_id=data["sample_id"],
            question=data["question"],
            expected_answer=data["expected_answer"],
            domain=LegalDomain(data["domain"]),
            difficulty=DifficultyLevel(data["difficulty"]),
            source_references=data.get("source_references", []),
            validated_by=data.get("validated_by", ""),
            validated_at=datetime.fromisoformat(data["validated_at"]) if data.get("validated_at") else None,
            validation_notes=data.get("validation_notes", ""),
            alternative_answers=data.get("alternative_answers", []),
            required_keywords=data.get("required_keywords", []),
        )


@dataclass
class EvaluationResult:
    """
    Evaluation result for a single sample or batch.
    
    Contains detailed metrics aligned with v2.0.0 KPIs.
    """
    sample_id: str
    adapter_id: str
    
    # Primary metrics
    accuracy: float  # Exact match score
    f1_score: float  # Token-level F1
    bleu_score: float  # BLEU-4 score
    rouge_l: float  # ROUGE-L score
    
    # Performance metrics
    latency_ms: float
    tokens_generated: int
    
    # Detailed results
    generated_answer: str
    is_correct: bool
    keyword_matches: int
    keyword_total: int
    
    # Error analysis
    error_type: Optional[str] = None
    error_details: Optional[str] = None
    
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sample_id": self.sample_id,
            "adapter_id": self.adapter_id,
            "accuracy": self.accuracy,
            "f1_score": self.f1_score,
            "bleu_score": self.bleu_score,
            "rouge_l": self.rouge_l,
            "latency_ms": self.latency_ms,
            "tokens_generated": self.tokens_generated,
            "generated_answer": self.generated_answer,
            "is_correct": self.is_correct,
            "keyword_matches": self.keyword_matches,
            "keyword_total": self.keyword_total,
            "error_type": self.error_type,
            "error_details": self.error_details,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


@dataclass
class RegressionAlert:
    """
    Regression alert when accuracy drops.
    
    v2.0.0 requirement: Alert on Accuracy drop > 5%
    """
    alert_id: str
    adapter_id: str
    metric_name: str
    baseline_value: float
    current_value: float
    threshold: float
    severity: str  # "warning" or "critical"
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    
    @property
    def drop_percentage(self) -> float:
        """Calculate percentage drop from baseline."""
        if self.baseline_value == 0:
            return 0.0
        return ((self.baseline_value - self.current_value) / self.baseline_value) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "alert_id": self.alert_id,
            "adapter_id": self.adapter_id,
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "drop_percentage": self.drop_percentage,
            "severity": self.severity,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
        }


class GoldenDataset:
    """
    Golden Dataset Manager for VCC-UDS3 v2.0.0
    
    Manages expert-validated evaluation data for adapter quality assurance:
    - 1000+ expert-validated QA pairs
    - Domain and difficulty stratification
    - Automated pre-deployment validation
    - Regression detection and alerting
    """
    
    REGRESSION_THRESHOLD = 0.05  # 5% accuracy drop triggers alert
    MIN_SAMPLES_FOR_EVALUATION = 100
    TARGET_SAMPLES = 1000
    
    def __init__(self, storage_backend: Any = None):
        """Initialize Golden Dataset manager."""
        self.storage = storage_backend
        self._samples: Dict[str, GoldenSample] = {}
        self._evaluation_history: List[Dict[str, Any]] = []
        self._baseline_metrics: Dict[str, float] = {}
        self._alerts: List[RegressionAlert] = []
        
    def add_sample(self, sample: GoldenSample) -> None:
        """Add a sample to the Golden Dataset."""
        self._samples[sample.sample_id] = sample
        
    def add_samples_batch(self, samples: List[GoldenSample]) -> int:
        """Add multiple samples at once."""
        for sample in samples:
            self.add_sample(sample)
        return len(samples)
    
    def get_sample(self, sample_id: str) -> Optional[GoldenSample]:
        """Get a sample by ID."""
        return self._samples.get(sample_id)
    
    def list_samples(
        self,
        domain: Optional[LegalDomain] = None,
        difficulty: Optional[DifficultyLevel] = None,
        limit: Optional[int] = None,
    ) -> List[GoldenSample]:
        """List samples with optional filtering."""
        samples = list(self._samples.values())
        
        if domain:
            samples = [s for s in samples if s.domain == domain]
        if difficulty:
            samples = [s for s in samples if s.difficulty == difficulty]
        if limit:
            samples = samples[:limit]
        
        return samples
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        samples = list(self._samples.values())
        
        domain_counts = {}
        difficulty_counts = {}
        
        for sample in samples:
            domain_counts[sample.domain.value] = domain_counts.get(sample.domain.value, 0) + 1
            difficulty_counts[sample.difficulty.value] = difficulty_counts.get(sample.difficulty.value, 0) + 1
        
        return {
            "total_samples": len(samples),
            "target_samples": self.TARGET_SAMPLES,
            "completion_percentage": (len(samples) / self.TARGET_SAMPLES) * 100,
            "by_domain": domain_counts,
            "by_difficulty": difficulty_counts,
            "validated_count": len([s for s in samples if s.validated_by]),
        }
    
    async def evaluate_adapter(
        self,
        adapter_id: str,
        inference_fn: callable,
        samples: Optional[List[GoldenSample]] = None,
    ) -> Dict[str, Any]:
        """Evaluate an adapter against the Golden Dataset."""
        import time
        
        samples = samples or list(self._samples.values())
        results: List[EvaluationResult] = []
        
        for sample in samples:
            start_time = time.time()
            try:
                generated = await inference_fn(sample.question)
            except Exception as e:
                logger.error(f"Error evaluating {sample.sample_id}: {e}")
                continue
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Calculate metrics
            accuracy = self._calculate_accuracy(generated, sample)
            f1_score = self._calculate_f1(generated, sample.expected_answer)
            
            keyword_matches = sum(
                1 for kw in sample.required_keywords
                if kw.lower() in generated.lower()
            )
            
            results.append(EvaluationResult(
                sample_id=sample.sample_id,
                adapter_id=adapter_id,
                accuracy=accuracy,
                f1_score=f1_score,
                bleu_score=0.0,
                rouge_l=0.0,
                latency_ms=latency_ms,
                tokens_generated=len(generated.split()),
                generated_answer=generated,
                is_correct=accuracy > 0.8,
                keyword_matches=keyword_matches,
                keyword_total=len(sample.required_keywords),
            ))
        
        # Aggregate
        aggregated = {
            "adapter_id": adapter_id,
            "accuracy": sum(r.accuracy for r in results) / len(results) if results else 0,
            "f1_score": sum(r.f1_score for r in results) / len(results) if results else 0,
            "avg_latency_ms": sum(r.latency_ms for r in results) / len(results) if results else 0,
            "evaluated_samples": len(results),
            "evaluated_at": datetime.utcnow().isoformat(),
        }
        
        self._evaluation_history.append(aggregated)
        return aggregated
    
    def _calculate_accuracy(self, generated: str, sample: GoldenSample) -> float:
        """Calculate accuracy."""
        gen_norm = generated.strip().lower()
        exp_norm = sample.expected_answer.strip().lower()
        
        if gen_norm == exp_norm:
            return 1.0
        
        for alt in sample.alternative_answers:
            if gen_norm == alt.strip().lower():
                return 1.0
        
        gen_tokens = set(gen_norm.split())
        exp_tokens = set(exp_norm.split())
        
        if not exp_tokens:
            return 0.0
        
        overlap = len(gen_tokens & exp_tokens)
        return overlap / len(exp_tokens)
    
    def _calculate_f1(self, generated: str, expected: str) -> float:
        """Calculate F1 score."""
        gen_tokens = set(generated.lower().split())
        exp_tokens = set(expected.lower().split())
        
        if not gen_tokens or not exp_tokens:
            return 0.0
        
        tp = len(gen_tokens & exp_tokens)
        precision = tp / len(gen_tokens)
        recall = tp / len(exp_tokens)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def set_baseline(self, metrics: Dict[str, float]) -> None:
        """Set baseline metrics for regression detection."""
        self._baseline_metrics = metrics.copy()
    
    def check_regression(
        self,
        current_metrics: Dict[str, Any],
        threshold: Optional[float] = None,
    ) -> List[RegressionAlert]:
        """Check for regression against baseline."""
        threshold = threshold or self.REGRESSION_THRESHOLD
        alerts = []
        
        for metric in ["accuracy", "f1_score"]:
            baseline = self._baseline_metrics.get(metric)
            current = current_metrics.get(metric)
            
            if baseline and current and baseline > 0:
                drop = (baseline - current) / baseline
                
                if drop > threshold:
                    alert = RegressionAlert(
                        alert_id=f"regression-{metric}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        adapter_id=current_metrics.get("adapter_id", "unknown"),
                        metric_name=metric,
                        baseline_value=baseline,
                        current_value=current,
                        threshold=threshold,
                        severity="critical" if drop > threshold * 2 else "warning",
                    )
                    alerts.append(alert)
                    self._alerts.append(alert)
        
        return alerts
