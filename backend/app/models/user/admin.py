from sqlalchemy import Column, Integer, ForeignKey

from app.models.user.user import User


class Admin(User):
    id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True, index=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def __repr__(self):
        return super().__repr__() + f"Admin(id={self.id!r})"
