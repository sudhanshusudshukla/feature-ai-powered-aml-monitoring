"""Alert repository for alert persistence."""
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.common.errors import OptimisticLockConflictError


class AlertRepository:
    """Repository for alert operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, alert: Alert) -> Alert:
        """Create a new alert."""
        self.db.add(alert)
        self.db.flush()
        return alert
    
    def get_by_id(self, alert_id: int) -> Alert | None:
        """Get alert by ID."""
        return self.db.query(Alert).filter(Alert.id == alert_id).first()
    
    def update_with_version(self, alert: Alert, expected_version: int) -> Alert:
        """
        Update alert with optimistic locking.
        Raises OptimisticLockConflictError if version mismatch.
        """
        result = self.db.query(Alert).filter(
            Alert.id == alert.id,
            Alert.version == expected_version
        ).update({
            "status": alert.status,
            "assigned_to_user_id": alert.assigned_to_user_id,
            "updated_at": alert.updated_at,
            "version": alert.version + 1
        })
        
        if result == 0:
            raise OptimisticLockConflictError("Alert version conflict")
        
        self.db.flush()
        return alert
    
    def generate_alert_number(self) -> str:
        """Generate a unique alert number."""
        # Get max alert ID to generate sequential number
        max_id = self.db.query(Alert.id).order_by(Alert.id.desc()).first()
        next_id = (max_id[0] + 1) if max_id else 1
        return f"ALT-{next_id:06d}"
