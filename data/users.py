import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    sites = orm.relationship("Site", back_populates="user")

    def __repr__(self):
        return f"<User> {self.id} {self.username} Сайты: {', '.join([s.name for s in self.sites])}"