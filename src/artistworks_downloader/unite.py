from __future__ import unicode_literals, absolute_import, print_function
from contextlib import suppress

import os
import itertools
import subprocess

import logbook

from artistworks_downloader.constants import LOG_PATH

__author__ = 'Omer'

logger = logbook.Logger(__name__)
logger.handlers.append(logbook.FileHandler(LOG_PATH, bubble=True, level=logbook.DEBUG))
logger.handlers.append(logbook.StderrHandler())


def unite_ts_videos(folder, delete_original=True):
    for r, d, files in os.walk(folder):
        it = itertools.groupby(sorted(files), lambda x: x.split('_part')[0])
        for group, file_list in it:

            file_list = list(file_list)  # don't exhaust iterator
            logger.debug('Group {} contains {} parts'.format(group, len(file_list)))
            if len(file_list) == 1:
                logger.debug('{} does not require processing'.format(group))
                continue

            file_paths = [os.path.join(r, f) for f in file_list]
            file_list_path = os.path.join(r, group + '_file_list.txt')

            # check no parts are missing! (from 0-max)
            # path/blah_part0.ts --> 0
            key_func = lambda x: int(x.split('_part')[1].split('.')[0])

            try:
                highest_part_no = key_func(max(file_paths, key=key_func))
            except ValueError as e:
                # example my_video_part_2.mp4 would throw exception on conversion to int
                logger.exception(e)
                continue

            if len(file_paths) != (highest_part_no + 1):
                logger.error('Found missing parts! not uniting!')
                return

            output_path = os.path.join(r, group + '.mp4')
            with open(file_list_path, 'w') as l:
                for f in sorted(file_paths, key=key_func):
                    print("file {}".format(repr(f)), file=l)
                    l.write('\r\n')

            logger.debug('Calling ffmpeg on file in {} , output {}'.format(file_list_path, output_path))
            try:
                subprocess.check_call(
                    ['ffmpeg', '-f', 'concat', '-i', file_list_path, '-bsf:a', 'aac_adtstoasc', '-c', 'copy',
                     output_path])
            except subprocess.CalledProcessError as e:
                logger.exception(e)
                delete_original = False

            os.remove(file_list_path)

            if delete_original:
                for f in file_paths:
                    os.remove(f)