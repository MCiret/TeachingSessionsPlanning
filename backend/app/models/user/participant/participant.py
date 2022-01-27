from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.user.user import User


if TYPE_CHECKING:
    from app.models.user.participant.participant_type import ParticipantType  # noqa
    from app.models.user.participant.participant_status import ParticipantStatus  # noqa
    from app.models.user.speaker import Speaker  # noqa
    from app.models.reservation import Reservation  # noqa


class Participant(User):
    id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True, index=True)

    type_id = Column(Integer, ForeignKey('participanttype.id'), index=True, nullable=False)  # one to many
    type = relationship("ParticipantType", back_populates="participants")

    status_id = Column(Integer, ForeignKey('participantstatus.id'), index=True, nullable=False)  # one to many
    status = relationship("ParticipantStatus", back_populates="participants")

    speaker_id = Column(Integer, ForeignKey('speaker.id'), index=True, nullable=False)  # one to many
    speaker = relationship("Speaker", back_populates="participants", foreign_keys=[speaker_id])

    reservation = relationship("Reservation", back_populates="participant", uselist=False)  # one to one

    sessions = relationship("Session", back_populates="participant")

    __mapper_args__ = {
        'polymorphic_identity': 'participant',
    }

    def __repr__(self):
        return super().__repr__() + (f"Participant(id={self.id!r}, status_id={self.status_id!r}, "
                                     f"type_id={self.type_id!r}, speaker_id={self.speaker_id!r})")
