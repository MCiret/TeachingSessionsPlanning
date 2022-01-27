from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.session.session import Session  # noqa: F401


class SessionStatus(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    sessions = relationship("Session", back_populates="status")  # many to one

    def __repr__(self):
        return (f"SessionStatus(id={self.id!r}, name={self.name!r})")
