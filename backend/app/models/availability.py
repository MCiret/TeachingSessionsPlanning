from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, Date, Time, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user.speaker import Speaker  # noqa
    from app.models.reservation import Reservation  # noqa


class Availability(Base):
    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, index=True, nullable=False)
    end_date = Column(Date, index=True, nullable=False)
    week_day = Column(Integer, index=True, nullable=False)
    time = Column(Time, index=True, nullable=False)

    speaker_id = Column(Integer, ForeignKey('speaker.id'), index=True, nullable=False)  # one to many
    speaker = relationship("Speaker", back_populates="availabilities")

    reservation = relationship("Reservation", back_populates="availability", uselist=False)  # one to one

    def __repr__(self):
        return (f"Availability(id={self.id!r}, start_date={self.start_date!s}, end_date={self.end_date!s}, "
                f"week_day={self.week_day!r}, time={self.time!s}, speaker_id={self.speaker_id!r})")
