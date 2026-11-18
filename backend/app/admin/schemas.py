"""Admin schemas for user and system management."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserListItem(BaseModel):
    """User list item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
