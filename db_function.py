from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from data import db_session
from data.sites import Site
from data.users import User
import requests
from bs4 import BeautifulSoup
import os
import logging
import sqlalchemy
db_session.global_init("db/parser.db")
engine = create_engine('sqlite:///db/parser.db')
Session = sessionmaker(bind=engine)

def get_id_username(username):
    with Session() as db_sess:
        user = db_sess.query(User).filter(User.username == username).first()
        return user.id

def get_id_username_with_session(username, db_sess):
    try:
        user_id = db_sess.query(User).filter(User.username == username).first().id
        return user_id
    except AttributeError:
        raise Exception(f"Пользователь {username} не найден")

def add_user(username):
    with Session() as db_sess:
        if not db_sess.query(User).filter(User.username == username).first():
            user = User()
            user.username = username
            db_sess.add(user)
            db_sess.commit()
            logging.info(f"Пользователь {username} успешно добавлен")
        else:
            raise Exception(f"Пользователь {username} уже существует")

def add_site(href, name, username):
    with Session() as db_sess:
        user_id = get_id_username_with_session(username, db_sess)
        if db_sess.query(Site).filter(Site.name == name, Site.user_id == user_id).first():
            raise Exception(f"Сайт c именем {name} у пользователя {username} уже существует")
        site = Site()
        site.href = href
        site.name = name
        site.user_id = user_id
        output_file = f"htmls/{name}_{username}.html"
        response = requests.get(href)
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(f"Сайт {href} не найден")
        soup = BeautifulSoup(response.text, 'html.parser')

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(str(soup.prettify()))
        site.html = output_file
        db_sess.add(site)
        db_sess.commit()
        logging.info(f"Сайт {name} успешно добавлен пользователю {username}")



def get_sites_userid(user_id):
    with Session() as db_sess:
        sites = db_sess.query(Site).options(joinedload(Site.user)).filter(Site.user_id == user_id).all()
        return sites


def get_sites_username(username):
    with Session() as db_sess:
        user_id = get_id_username_with_session(username, db_sess)
        sites = db_sess.query(Site).options(joinedload(Site.user)).filter(Site.user_id == user_id).all()
        return sites

def delete_site(name, username):
    with Session() as db_sess:
        user_id = get_id_username_with_session(username, db_sess)
        site = db_sess.query(Site).options(joinedload(Site.user)).filter(Site.user_id == user_id,
                                                                         Site.name == name).first()
        if site:
            os.remove(f"htmls/{name}_{user_id}.html")
            db_sess.delete(site)
            db_sess.commit()
            logging.info(f"Сайт {name} у пользователя {username} успешно удален")
        else:
            raise Exception(f"Сайт {name} у пользователя {username} не найден")