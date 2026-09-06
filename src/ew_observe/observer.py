"""Public observer class combining step- and candidate-centric microscopes."""

from __future__ import annotations

from .decision import EWObserver as _DecisionEWObserver
from .lifecycle import CandidateLifecycleTrace, trace_candidate_lifecycle


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
