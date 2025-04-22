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
    user = orm.relationship("User", back_populates="sites")