#!/usr/bin/env python3

import os
import time
import sys

from transcoder import database

MAX_WORKERS = 15
work_db = "/transcoder/transcoder_database.db"
db = database.Database(work_db)
input_dir = "/files_input_dir"
output_dir = "/files_output_dir"


# Cчитаем количество активных воркеров
def count_active_workers():
    db.check_workers_status()
    active_workers = db.count_active_workers()
    return active_workers


# Запускаем сервис
def start():
    while True:
        active_workers = count_active_workers()
        print(f"Active workers now - {active_workers}")
        if active_workers >= MAX_WORKERS:
            print("Max workers limit reached, " +
                  f"active workers now - {active_workers}")
            time.sleep(30)
        else:
            input_file = db.get_film_for_transcode()
            if type(input_file) == str:
                print("Nothing to transcode")
                break
            input_file = input_file[0]
            print(f"Start transcoder, file - {input_file}")
            os.system("/transcoder_next/transcoder_next/transcoder_worker.py " +
                      f"\"{work_db}\" \"{input_file}\" \"{output_dir}\" &")
            time.sleep(5)

# Создаем базу
def create_new_db():
    db.create_new_db()
    db.fill_the_base("all_files_in_input_dir", input_dir)

argument = sys.argv[1]
if argument == "createdb":
    create_new_db()
elif argument == "start":
    start()
    print("Starting transcoder!")
else:
    print("Invalid or not given argument! Available arguments:")
    print("createdb")
    print("start")
