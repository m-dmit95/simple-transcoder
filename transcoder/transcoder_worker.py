#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import time

import database


class Transcoder:
    # max output parameters
    p_weight = 1920
    p_height = 1080
    p_bitrate = 5242880
    b_maxrate = '5M'
    p_audiobit = 192000

    def __init__(self, db, input_file, output_dir) -> None:
        self.db = database.Database(db)
        self.input_file = input_file

        self.input_filename = os.path.basename(input_file)
        self.output_file = f"{output_dir}{self.input_filename}"

    # Записываем пид данного транскодера в базу
    def write_pid(self):
        pid = str(os.getpid())
        self.db.write_pid(pid, self.input_file)

    # Собираем исходную инфу с файла
    def input_info(self):
        mediainfo = f"mediainfo \"{self.input_file}\""
        In_reso_w = f"{mediainfo} --Inform=\"Video;%Width%\""
        In_reso_w = os.popen(In_reso_w).read()

        In_reso_h = f"{mediainfo} --Inform=\"Video;%Height%\""
        In_reso_h = os.popen(In_reso_h).read()

        In_aspect_ratio = f"{mediainfo} --Inform=\"Video;%%DisplayAspectRatio/String%%\""
        In_aspect_ratio = os.popen(In_aspect_ratio).read()

        In_bitrate = f"{mediainfo} --Inform=\"Video;%BitRate%\""
        In_bitrate = os.popen(In_bitrate).read()
        if len(In_bitrate) == 0:
            In_bitrate = f"{mediainfo} --Inform=\"General;%OverallBitRate%\""
            In_bitrate = os.popen(In_bitrate).read()
            if len(In_bitrate) == 0:
                In_bitrate = f"{mediainfo} --Inform=\"Video;%BitRate_Nominal%\""

        In_audiobit = f"{mediainfo} --Inform=\"Audio;%BitRate%\" | head -1"
        In_audiobit = os.popen(In_audiobit).read()

        try:
            In_reso_w = int(In_reso_w.strip("\n"))
        except ValueError:
            In_reso_w = self.p_weight

        try:
            In_reso_h = int(In_reso_h.strip('\n'))
        except ValueError:
            In_reso_h = self.p_height

        try:
            In_aspect_ratio = In_aspect_ratio.strip('\n')
        except ValueError:
            In_aspect_ratio = '1,78:1'

        try:
            In_bitrate = int(In_bitrate.strip('\n'))
        except ValueError:
            In_bitrate = self.p_bitrate

        try:
            In_audiobit = int(In_audiobit.strip('\n'))
        except ValueError:
            In_audiobit = self.p_audiobit

        self.In_reso_w = In_reso_w
        self.In_reso_h = In_reso_h
        self.In_aspect_ratio = In_aspect_ratio
        self.In_bitrate = In_bitrate
        self.In_audiobit = In_audiobit

    def crop_for_profile(self):
        if self.In_reso_w > self.p_weight and self.In_aspect_ratio == '1,78:1':
            reso_w = self.p_weight
            reso_h = self.p_height
        elif self.In_reso_w > self.p_weight and self.In_aspect_ratio != '1,78:1':
            reso_w = self.p_weight
            reso_h = self.In_reso_h*hd_w/self.In_reso_w
        elif self.In_reso_w == self.p_weight and self.In_reso_h > self.p_height:
            reso_w = self.In_reso_w
            reso_h = self.p_height
        else:
            reso_w = self.In_reso_w
            reso_h = self.In_reso_h

        self.reso_w = reso_w
        self.reso_h = reso_h

    # Пересчитываем параметры для транскодирования
    def bitrate(self):
        if self.In_bitrate > self.p_bitrate:
            bitrate = self.p_bitrate
            max_rate = self.b_maxrate
        else:
            bitrate = self.In_bitrate
            max_rate = int(float(self.In_bitrate)*1.5)

        if self.In_audiobit > self.p_audiobit:
            a_bitrate = self.p_audiobit
        else:
            a_bitrate = self.In_audiobit

        self.bitrate = bitrate
        self.max_rate = max_rate
        self.a_bitrate = a_bitrate

    def check_ffmpeg(self):
        check_ffmpeg_query = (f"ps aux | grep \"{self.input_file}\" " +
                              "| grep -v grep | wc -l")
        check_ffmpeg_work = subprocess.Popen(check_ffmpeg_query,
                                             stdout=subprocess.PIPE,
                                             shell=True)
        check_ffmpeg_work = check_ffmpeg_work.communicate()[0]
        check_ffmpeg_work = check_ffmpeg_work.decode()
        check_ffmpeg_work = check_ffmpeg_work.strip('\n')
        return check_ffmpeg_work

    # Запускаем транскодирование
    def launch_transcoding(self):
        # reso_w = str(self.reso_w)
        # reso_h = str(self.reso_h)
        # bitrate = str(self.bitrate)
        # reso_w = str(self.reso_w)

        ffmpeg_in = ("ffmpeg -y -vsync 0 -hwaccel cuda -i " +
                     f"\"{self.input_file}\" -c:v h264_nvenc -sn -s " +
                     f"{self.reso_w}x{self.reso_h} -b:v {self.bitrate} " +
                     f"-c:a libfdk_aac -b:a {self.a_bitrate} -f mp4 -r 24 " +
                     f"-bt 30 -bufsize 5M -maxrate {self.max_rate} " +
                     "-color_primaries 1 -color_trc 1 -colorspace 1 " +
                     f"\"{self.output_file}\" " +
                     f"2>/var/log/ffmpeg/\"{self.input_filename}\".log")
        print(f"ffmpeg_in: {ffmpeg_in}")
        os.popen(ffmpeg_in).read()
        if int(self.check_ffmpeg()):
            time.sleep(60)

    def check_output(self):
        size_output = os.path.getsize(self.output_file)
        if size_output == 0:
            self.db.retry_film(self.input_file)
            print(f"Transcoder not complete file: {self.input_file}")
            sys.exit()
        else:
            self.db.set_complete(self.input_file)
            print(f"Transcoding complete! File: {self.input_file}")

    def replace_input_file(self):
        print(f"Move output file to input file {self.input_file}")
        shutil.move(self.output_file, self.input_file)
        print(f"Complete! - Move output file to input file {self.input_file}")


db = sys.argv[1]
file = sys.argv[2]
output_dir = sys.argv[3]

transcoder = Transcoder(db, file, output_dir)

transcoder.write_pid()
transcoder.input_info()
transcoder.crop_for_profile()
transcoder.bitrate()
transcoder.launch_transcoding()
transcoder.check_ffmpeg()
transcoder.check_output()

# transcoder.replace_input_file()
