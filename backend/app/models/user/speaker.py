from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.user.user import User

if TYPE_CHECKING:
     from participant.participant import Participant  # noqa
     from app.models.availability import Availability  # noqa


class Speaker(User):
    id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True, index=True)

    slot_time = Column(Integer, nullable=False, index=True)
    # many to one :
    participants = relationship("Participant", back_populates="speaker", foreign_keys="Participant.speaker_id")
    availabilities = relationship("Availability", back_populates="speaker")  # many to one

    __mapper_args__ = {
        'polymorphic_identity': 'speaker',
    }

    def __repr__(self):
        return super().__repr__() + f"Speaker(id={self.id!r}, slot_time={self.slot_time!r})"
