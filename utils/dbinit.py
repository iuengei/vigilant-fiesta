import os
import sqlite3

base_dir = os.path.dirname(os.path.abspath(__file__))
sql_dir = os.path.join(base_dir, 'sql')
BASE_DIR = os.path.dirname(base_dir)


def load_db(curs, datafile, conn):
    file = open(os.path.join(sql_dir, datafile), encoding='utf8')
    rows = [line for line in file]
    if rows:
        for sql in rows:
            curs.execute(str(sql))
        try:
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()


def db_init():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))
    curs = conn.cursor()
    sql_files = [name for name in os.listdir(sql_dir) if name.endswith('sql')]

    for sql_file in sql_files:
        table_name = sql_file.split('.')[0][5:]
        print(str(table_name) + ' init')
        # try:
        #     curs.execute('DROP TABLE ' + str(table_name))
        # except:
        #     print("table did not exist")
        #
        # curs.execute('CREATE TABLE ' + str(table_name))
        try:
            load_db(curs, sql_file, conn)
        except sqlite3.IntegrityError:
            continue

    conn.close()


if __name__ == '__main__':
    db_init()
