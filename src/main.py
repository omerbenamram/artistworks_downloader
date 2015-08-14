from __future__ import unicode_literals, absolute_import

import argparse
import os
import shelve
from pathlib import Path

import logbook

from artistworks_downloader.constants import DEFAULT_OUTPUT_DIRECTORY, LOG_PATH
from artistworks_downloader.webdriver import ArtistWorkScraper
from artistworks_downloader.video_downloader import AsyncDownloader, get_valid_filename
from artistworks_downloader.unite import unite_ts_videos

parser = argparse.ArgumentParser(description='Grabs videos from artistworks')
parser.add_argument('--username', type=str, required=True,
                    help='Username to connect to artistworks')
parser.add_argument('--password', type=str, required=True,
                    help='Password to connect to artistworks')
parser.add_argument('--output_dir', type=str, nargs='?', default=DEFAULT_OUTPUT_DIRECTORY,
                    help='specify output directory')
parser.add_argument('--fetch_extras', default=False, action='store_true',
                    help='whether to download extra lesson objects (such as slow motion etc..)')
parser.add_argument('--fetch_masterclasses', default=False, action='store_true',
                    help='whether to download student exchanges for lessons')
parser.add_argument('--use_firefox', default=False, action='store_true',
                    help='whether to use firefox instead of chrome webdriver')
parser.add_argument('--use_virtual_display', default=False, action='store_true',
                    help='whether to use a virtual display for running in headless mode (linux only)')
parser.add_argument('--resume', default=False, action='store_true',
                    help='simply resume downloading, dont connect to artistworks')
parser.add_argument('--root_folder', type=str, required=True,
                    help="Name of root folder to save files in (Artist's name for example)")

links_group = parser.add_mutually_exclusive_group(required=True)
links_group.add_argument('--department', type=int,
                         help='Department number to be scraped')
links_group.add_argument('--only_lessons', type=str, nargs='*',
                         help='download only specified lessons')

logger = logbook.Logger(__name__)
logger.handlers.append(logbook.FileHandler(LOG_PATH, bubble=True, level='DEBUG'))
logger.handlers.append(logbook.StderrHandler())

args = parser.parse_args()

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)


def main():
    if args.use_virtual_display:
        import pyvirtualdisplay

        display = pyvirtualdisplay.Display(visible=0, size=(800, 600))
        display.start()

    scraper = ArtistWorkScraper(fetch_extras=args.fetch_extras, use_firefox=args.use_firefox)

    if not args.resume:
        scraper.login_to_artistworks(username=args.username, password=args.password)

    if args.only_lessons:
        lesson_ids = args.only_lessons
        department_name = 'Misc lessons'
    else:
        department_name = scraper.get_department_name(args.department)
        lesson_ids = scraper.get_all_lesson_ids_for_department(args.department)

    lessons_db = shelve.open(os.path.join(args.output_dir, department_name + '_lessons.db'))
    masterclasses_db = shelve.open(os.path.join(args.output_dir, department_name + '_masterclasses.db'))

    for lesson_id in lesson_ids:
        if lesson_id not in lessons_db:
            lessons_db[lesson_id] = scraper.get_lesson_by_id(lesson_id)

        if args.fetch_masterclasses:
            for masterclass_id in lessons_db[lesson_id].masterclass_ids:
                if masterclass_id not in masterclasses_db:
                    masterclasses_db[masterclass_id] = scraper.get_masterclass_by_id(masterclass_id)

    # start downlaoding

    downloader = AsyncDownloader()

    for lesson in lessons_db.values():
        lesson_output_folder_path = Path(args.output_dir).joinpath(args.root_folder).joinpath(department_name).joinpath(
            get_valid_filename(lesson.name))

        for lesson_link in lesson.links:
            downloader.download_link(lesson_link, lesson_output_folder_path)

        if args.fetch_masterclasses:
            for masterclass_id in lesson.masterclass_ids:
                masterclass = masterclasses_db[masterclass_id]
                masterclass_output_folder_path = lesson_output_folder_path.joinpath(masterclass.name)
                for masterclass_link in masterclass.links:
                    downloader.download_link(masterclass_link, masterclass_output_folder_path)

    downloader.run()

    unite_ts_videos(os.path.join(args.output_dir, args.root_folder))

    scraper.exit()


