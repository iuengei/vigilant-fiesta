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
    # import random
    # def id_card():
    #     id_card = '410323' + str(random.choice(range(1980, 1993))) + str(random.choice(range(1, 13))).rjust(2, '0') + \
    #               str(random.choice(range(1, 31))).rjust(2, '0') + str(random.choice(range(1, 100))).rjust(3, '0') + \
    #               random.choice('0123456789X')
    #     return id_card
    #
    # for i in range(1, 71):
    #     _dict = {'name': '班主任' + str(i),
    #              'sex': random.choice([1, 0]),
    #              'branch': random.choice(range(1, 9)),
    #              'age': random.choice(range(20, 30)),
    #              'id_card': id_card(),
    #              'mobile': random.choice(range(13213102645, 19999999999))}
    #     try:
    #         accounts_models.Supervisor.objects.create(**_dict)
    #     except Exception as e:
    #         print(e)
    #         _id_card = id_card()
    #         _dict.update({'id_card': _id_card})
    #         try:
    #             accounts_models.Supervisor.objects.create(**_dict)
    #         except:
    #             continue
    #
    # supervisor_dict = {}
    #
    # for i in range(1, 551):
    #     _dict = {'name': '学生' + str(i),
    #              'sex': random.choice(range(0, 2)),
    #              'branch': random.choice(range(1, 9)),
    #              'grade': random.choice(range(1, 13)),
    #              'id_card': id_card()}
    #     branch = _dict.get('branch')
    #     if branch in supervisor_dict:
    #         _dict['supervisor_id'] = random.choice(supervisor_dict[branch])
    #     else:
    #         supervisor_dict[branch] = accounts_models.Supervisor.objects.filter(branch=branch).values_list('id',
    #                                                                                                        flat=True)
    #         _dict['supervisor_id'] = random.choice(supervisor_dict[branch])
    #     try:
    #         models.Student.objects.create(**_dict)
    #     except Exception as e:
    #         print(e)
    #         continue
    #
    # for i in range(1, 801):
    #     _dict = {'name': '教师' + str(i),
    #              'sex': random.choice([1, 0]),
    #              'branch': random.choice(range(1, 9)),
    #              'age': random.choice(range(20, 51)),
    #              'work_type': random.choice([1, 0]),
    #              'id_card': id_card(),
    #              'subject': random.choice(range(1, 10)),
    #              'mobile': random.choice(range(13213102645, 19999999999))}
    #     try:
    #         accounts_models.Teacher.objects.create(**_dict)
    #     except Exception as e:
    #         print(e)
    #         _id_card = id_card()
    #         _dict.update({'id_card': _id_card})
    #         try:
    #             accounts_models.Teacher.objects.create(**_dict)
    #         except:
    #             continue
    #
    # teacher_count = accounts_models.Teacher.objects.count()
    # for i in range(1, teacher_count + 1):
    #     try:
    #         accounts_models.Teacher.objects.get(id=i).grades.add(random.choice(random.choices(list(range(1, 13)), k=3)))
    #     except:
    #         continue
