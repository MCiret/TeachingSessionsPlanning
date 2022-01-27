from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, Date, Time, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user.participant.participant import Participant  # noqa: F401
    from app.models.session.session_type import SessionType  # noqa: F401
    from app.models.session.session_status import SessionStatus  # noqa: F401


class Session(Base):
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    time = Column(Time, index=True, nullable=False)
    comments = Column(Text, index=True)

    participant_id = Column(Integer, ForeignKey('participant.id'), index=True, nullable=False)  # one to many
    participant = relationship("Participant", back_populates="sessions")

    type_id = Column(Integer, ForeignKey('sessiontype.id'), index=True, nullable=False)  # one to many
    type = relationship("SessionType", back_populates="sessions")

    status_id = Column(Integer, ForeignKey('sessionstatus.id'), index=True, nullable=False)  # one to many
    status = relationship("SessionStatus", back_populates="sessions")
