from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from data import db_session
from data.sites import Site
from data.users import User
import requests
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime
import sqlalchemy

db_session.global_init("db/parser.db")
engine = create_engine('sqlite:///db/parser.db')
Session = sessionmaker(bind=engine)
import json


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


def add_user(username, tg_id):
    with Session() as db_sess:
        if not db_sess.query(User).filter(User.username == username).first():
            user = User()
            user.username = username
            user.tg_id = tg_id
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


def get_all_users():
    with Session() as db_sess:
        users = db_sess.query(User).all()
        return users


def delete_site(name, username):
    with Session() as db_sess:
        user_id = get_id_username_with_session(username, db_sess)
        site = db_sess.query(Site).options(joinedload(Site.user)).filter(Site.user_id == user_id,
                                                                         Site.name == name).first()
        if site:
            os.remove(f"htmls/{name}_{username}.html")
            db_sess.delete(site)
            db_sess.commit()
            logging.info(f"Сайт {name} у пользователя {username} успешно удален")
        else:
            raise Exception(f"Сайт {name} у пользователя {username} не найден")


def add_history(site_id, changes):
    with Session() as db_sess:
        site = db_sess.query(Site).filter(Site.id == site_id).first()
        if site:
            history = []
            if site.history:
                try:
                    history = json.loads(site.history)
                except json.JSONDecodeError:
                    history = []
            change = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "change": changes}
            history.append(change)
            site.history = json.dumps(history)
            db_sess.commit()
            logging.info(f"Изменения на сайте '{site.name}' успешно добавлены")


def get_history(site_id):
    with Session() as db_sess:
        history = db_sess.query(Site).filter(Site.id == site_id).first().history.all()
        return history


def get_history_by_username(username):
    with Session() as db_sess:
        user_id = get_id_username_with_session(username, db_sess)
        sites = db_sess.query(Site).filter(Site.user_id == user_id).all()
        history = []
        for site in sites:
            if site.history:
                try:
                    site_history = json.loads(site.history)
                    for change in site_history:
                        history.append(f"<b>{site.name}</b>\n{site.href}\n{change['date']}\n{change['change']}\n")
                except json.JSONDecodeError:
                    history.append(f"<b>{site.name}</b> ({site.href}):\nОшибка чтения истории\n")
        return history if history else ["История изменений пуста"]
