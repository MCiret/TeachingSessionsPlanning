from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user.participant.participant import Participant  # noqa
    from app.models.availability import Availability  # noqa


class Reservation(Base):
    participant_id = Column(Integer, ForeignKey('participant.id'), primary_key=True, index=True)
    availability_id = Column(Integer, ForeignKey('availability.id'), primary_key=True, index=True)

    participant = relationship("Participant", back_populates="reservation", uselist=False)
    availability = relationship("Availability", back_populates="reservation", uselist=False)
