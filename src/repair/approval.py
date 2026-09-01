"""Human approval gate for repair application."""

from datetime import datetime, timezone
from typing import Optional
from src.scenarios.models import RepairProposal


class ApprovalError(Exception):
    """Raised when an action requires human approval that was not granted."""
    pass


class HumanApprovalGate:
    """Enforces human-in-the-loop checkpoint before any repair is applied."""

    @staticmethod
    def approve_proposal(proposal: RepairProposal, approver_name: str = "Human Reviewer") -> RepairProposal:
        """Explicitly records human approval of a proposed repair."""
        approver_name = approver_name.strip()
        if not approver_name:
            raise ApprovalError("A non-empty human approver name is required.")
        proposal.approved_by_human = True
        proposal.approved_by = approver_name
        proposal.approval_timestamp = datetime.now(timezone.utc).isoformat()
        return proposal

    @staticmethod
    def assert_approved(proposal: Optional[RepairProposal]) -> None:
        """Verifies that the repair proposal has been explicitly approved by a human."""
        if proposal is None:
            raise ApprovalError("No repair proposal exists to approve.")
        if not proposal.approved_by_human:
            raise ApprovalError(
                f"Human approval required for repair '{proposal.repair_name}' ({proposal.repair_id}). "
                "Consequential migration changes cannot be applied without explicit human approval."
            )
