from sqlalchemy import Boolean, Column, Integer, String

from app.db.base_class import Base


class User(Base):
    """
    Base class of Admin, Speaker and Participant.
    """
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_api_key = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)

    profile = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': profile,
        'with_polymorphic': '*'
    }

    def __repr__(self):
        return (f"User(id={self.id!r}, email={self.email!r}, first_name={self.first_name!r}, "
                f"last_name={self.last_name!r}, isactive={self.is_active!r}, profile={self.profile!r})")
