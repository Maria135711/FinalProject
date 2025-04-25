from data import db_session
from data.sites import Site
from data.users import User
from sqlalchemy.orm import sessionmaker, joinedload
from db_function import *
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(name)s | %(message)s',
    level=logging.INFO
)

def main():
    add_user("admin")
    add_site("https://vk.com", "vk", "admin")
if __name__ == "__main__":
    main()
