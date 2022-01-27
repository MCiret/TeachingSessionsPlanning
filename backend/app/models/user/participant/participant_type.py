from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user.participant.participant import Participant  # noqa


class ParticipantType(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    nb_session_week = Column(Integer, index=True, nullable=False)
    participants = relationship("Participant", back_populates="type")

    def __repr__(self):
        return (f"ParticipantType(id={self.id!r}, name={self.name!r}, nb_session_week={self.nb_session_week!r})")
