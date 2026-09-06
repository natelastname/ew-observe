"""Public observer class combining the EW microscopes."""

from __future__ import annotations

from .decision import EWObserver as _DecisionEWObserver
from .lifecycle import CandidateLifecycleTrace, trace_candidate_lifecycle
from .queue_heads import QueueHeadTrace, trace_queue_heads


class EWObserver(_DecisionEWObserver):
    """Instrumented view of a supplied real EW prefix."""

    def trace_candidate_lifecycle(
        self,
        value: int,
        *,
        start: int,
        stop: int,
    ) -> CandidateLifecycleTrace:
        """Track one fixed candidate through consecutive EW selection states."""

        return trace_candidate_lifecycle(self, value, start=start, stop=stop)

    def trace_queue_heads(self, n: int) -> QueueHeadTrace:
        """Compress one step to exact queues with last-used frontier and current head."""

        return trace_queue_heads(self, n)
