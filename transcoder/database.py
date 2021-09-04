#!/usr/bin/env python3

import sqlite3
import os


class Database:
    INPUT_TABLE = "filename text PRIMARY KEY, pid int, complete bool"

    def __init__(self, db) -> None:
        # путь к базе, например "/transdoder/database.db"
        self.db = db

    # Функция для создания новой базы данных
    def create_new_db(self):
        print("Creating new database...")
        # Проверяем, что данного файла не существует
        if os.path.exists(self.db):
            message = ("---------------------- \n" +
                       "ERROR: Cannot create new database! \n" +
                       f"File '{self.db}' already exists! \n" +
                       "----------------------")
            return print(message)

        conn = sqlite3.connect(self.db)
        conn.cursor().execute(f"CREATE TABLE input ({self.INPUT_TABLE})")
        conn.commit()
        return f"Database '{self.db}' successfully created!"

    # Функция для заполнения базы
    def fill_the_base(self, method, input_dir):
        file_list = []
        methods_list = ["all_files_in_input_dir"]

        if method == "all_files_in_input_dir":
            # Формируем список фильмов
            for root, dirs, files in os.walk(input_dir, topdown=False):
                for name in files:
                    print(os.path.join(root, name))
                    file_list.append(os.path.join(root, name))
        else:
            message = ("ERROR: Invalid method. \n" +
                       f"Available methods: \n{methods_list}")
            return print(message)

        # Добавляем фильмы в базу:
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        for file in file_list:
            # Проверяем, что данного файла нет в базе
            check_db_query = f"SELECT * FROM input WHERE filename=\"{file}\""
            cursor.execute(check_db_query)
            fileInDatabase = cursor.fetchall()
            if len(fileInDatabase) == 0:
                insert_query = ("INSERT OR IGNORE INTO input VALUES " +
                                f"(\"{file}\", \"0\", \"False\")")
                print(f"Adding '{file}' into DB")
                cursor.execute(insert_query)
            else:
                print(f"Cannot add '{file}' into DB - row exists")
        conn.commit()
        return print("Complete.")

    # Функция, которая дает фильм для транскодирования:
    def get_film_for_transcode(self):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        get_films_query = ("SELECT filename FROM input WHERE " +
                           "complete=\"False\" and pid=\"0\" LIMIT 1")
        cursor.execute(get_films_query)
        result = cursor.fetchall()
        if len(result) == 0:
            conn.commit()
            return "Nothing to transcode"

        film_for_transcode = result[0]
        return film_for_transcode

    # Функция, которая считает количество активных воркеров:
    def count_active_workers(self):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        count_query = ("SELECT count(*) FROM input " +
                       "WHERE pid!=0 and complete is False")
        cursor.execute(count_query)
        count_result = cursor.fetchall()
        # active_workers = int(re.search("\d", str(count_result[0])).group())
        active_workers = count_result[0][0]
        conn.commit()
        return active_workers

    # Проверка на активность процесса по пиду
    def check_pid(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    # Функция, которая проверяет статус воркеров
    def check_workers_status(self):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        workers_query = ("SELECT * FROM input " +
                         "WHERE pid!=0 and complete=False")
        cursor.execute(workers_query)
        list_for_check = cursor.fetchall()
        for row in list_for_check:
            pid = int(row[1])
            if self.check_pid(pid) is False:
                update_query = f"UPDATE input SET pid=0 WHERE pid={pid}"
                cursor.execute(update_query)

    # Записываем пид в базу
    def write_pid(self, pid, file):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        update_pid_query = ("UPDATE input SET " +
                            f"pid={pid} WHERE filename=\"{file}\"")
        cursor.execute(update_pid_query)
        conn.commit()

    def retry_film(self, file):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        query_retry = ("UPDATE input SET complete=2 WHERE " +
                       f"filename=\"{file}\"")
        cursor.execute(query_retry)
        conn.commit()

    def set_complete(self, file):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        query_retry = ("UPDATE input SET complete=True WHERE " +
                       f"filename=\"{file}\"")
        cursor.execute(query_retry)
        conn.commit()

# db = Database("test123.db")
# print(db.get_film_for_transcode())
