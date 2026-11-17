"""Rules repository for catalog and version lookup."""
from sqlalchemy.orm import Session

from app.rules.models import DetectionRule, RuleVersion


class RulesRepository:
    """Repository for detection rules and versions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_rules(self) -> list[DetectionRule]:
        """Retrieve all active detection rules."""
        return self.db.query(DetectionRule).filter(
            DetectionRule.is_active == True
        ).all()
    
    def get_rule_by_code(self, rule_code: str) -> DetectionRule | None:
        """Get rule by code."""
        return self.db.query(DetectionRule).filter(
            DetectionRule.rule_code == rule_code
        ).first()
    
    def get_current_rule_version(self, rule_id: int) -> RuleVersion | None:
        """Get the most recent rule version for a rule."""
        return self.db.query(RuleVersion).filter(
            RuleVersion.rule_id == rule_id
        ).order_by(RuleVersion.version_number.desc()).first()
    
    def get_all_current_versions(self) -> dict[str, RuleVersion]:
        """Get current version for each active rule, keyed by rule code."""
        active_rules = self.get_active_rules()
        versions = {}
        for rule in active_rules:
            version = self.get_current_rule_version(rule.id)
            if version:
                versions[rule.rule_code] = version
        return versions
