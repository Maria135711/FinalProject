from data import db_session

def main():
    db_session.global_init("db/users.db")