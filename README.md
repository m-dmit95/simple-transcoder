# simple_transcoder

Транскодер для видеоконтента. Работает на основе python и ffmpeg.

## Описание

Данный проект позволяет автоматизированно транскодировать любое количество видеофайлов под единый стандарт - видео в кодеке H264, аудио в кодеке AAC.

## Требования

* Linux

    Я использовал Ubuntu Server 20.04, на других дистрибутивах сервис не тестировался.

* Наличие видеокарты NVIDIA

    Для работы сервиса необходимо наличие видеокарты NVIDIA c поддержкой NVENC. Список поддерживаемых видеокарт можно посмотреть на сайте NVIDIA - https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new#Encoder .

    > Сервис тестировался на картах 1080 и 2080 Super.

* Пропиетарный драйвер NVIDIA

    Я использовал драйвер версии 465.19.01

* ffmpeg

    Необходимо собрать ffmpeg из исходников со следующей конфигурацией:

    ```
    --enable-nonfree --enable-cuda-sdk --enable-libnpp --enable-gpl --enable-libx264 --enable-cuda --enable-cuvid --enable-nvdec --enable-nvenc --enable-libfdk-aac --extra-cflags=-I/usr/local/cuda/include --extra-ldflags=-L/usr/local/cuda/lib64
    ```

* Python 3

## Алгоритм работы

Сервис может создать sqlite3-БД и добавить в таблицу input все файлы, которые находятся в *input-каталоге*. Если файл находится в подкаталогах - он тоже добавляется в базу.

Затем сервис начинает по очереди транскодировать файлы из таблицы `input` и складывает результаты в *output-каталог*. Когда файл готов - в таблице `input` в поле `complete` устанавливается значение `1`.

## Как использовать

Склонируйте данный репозиторий на подготовленный сервер.

1. Укажите параметры в main.py:

   * `MAX_WORKERS` - количество одновременно запущенных процессов транскодирования
   * `work_db` - путь к базе данных
   * `input_dir` - каталог с видеофайлами, которые необходимо транскодировать
   * `output_dir` - каталог для транскодированных файлов.

2. Создайте базу - запустите скрипт `main.py` с параметром `createdb`
   
    ``` bash
    /transcoder/main.py createdb
    ```

3. Начните транскодирование - запустите скрипт `main.py` с параметром `createdb`
   
    ``` bash
    /transcoder/main.py start
    ```

Готово.

Вывод ffmpeg будет логгироваться в `/var/log/ffmpeg/`.

## В планах на разработку:

Сервис готов к использованию, но совершенству нет предела.

* Добавить более красивое логгирование
* Добавить потоковый режим работы
* Добавить статистику
* И так далее...