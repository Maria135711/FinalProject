import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

class Site(SqlAlchemyBase):
    __tablename__ = 'sites'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    href = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    html = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    user = orm.relationship("User", back_populates="sites")

    def __repr__(self):
        return f"<Site> {self.id} {self.name}; Пользователь: {self.user.id} {self.user.username}"