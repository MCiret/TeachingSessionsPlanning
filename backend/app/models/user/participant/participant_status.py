from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user.participant.participant import Participant  # noqa


class ParticipantStatus(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    participants = relationship("Participant", back_populates="status")  # many to one

    def __repr__(self):
        return (f"ParticipantStatus(id={self.id!r}, name={self.name!r})")
