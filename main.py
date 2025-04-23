from data import db_session
from data.sites import Site
from data.users import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///db/parser.db')
Session = sessionmaker(bind=engine)

def add_user(username):
    with Session() as db_sess:
        user = User()
        user.username = username
        db_sess.add(user)
        db_sess.commit()

def add_site(href, name, html, user_id):
    with Session() as db_sess:
        site = Site()
        site.href = href
        site.name = name
        site.user_id = user_id
        db_sess.add(site)
        db_sess.commit()

def main():
    db_session.global_init("db/parser.db")
    # user = User()
    # user.username = "test"
    db_sess = db_session.create_session()
    # db_sess.add(user)
    # db_sess.commit()
    user = db_sess.query(User).first()
    print(user)

if __name__ == "__main__":
    main()