import argparse
import asyncio
import os
import shelve
from pathlib import Path

import logbook

from artistworks_downloader.constants import DEFAULT_OUTPUT_DIRECTORY, LOG_PATH
from artistworks_downloader.webdriver import ArtistWorkScraper
from artistworks_downloader.video_downloader import async_download_video, wait_with_progress, get_valid_filename

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

links_group = parser.add_mutually_exclusive_group(required=True)
links_group.add_argument('--department', type=int,
                         help='Department number to be scraped')
links_group.add_argument('--only_lessons', type=str, nargs='*',
                         help='download only specified lessons')

logger = logbook.Logger(__name__)
logger.handlers.append(logbook.FileHandler(LOG_PATH, bubble=True))
logger.handlers.append(logbook.StderrHandler())

args = parser.parse_args()

LESSONS_DB_PATH = str(Path(args.output_dir).joinpath('lessons.db'))
MASTERCLASSES_DB_PATH = str(Path(args.output_dir).joinpath('masterclasses.db'))


if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

lessons_db = shelve.open(LESSONS_DB_PATH)
masterclasses_db = shelve.open(MASTERCLASSES_DB_PATH)


def download_link(link, output_path):
    if not output_path.exists():
        os.makedirs(str(output_path))

    filename = get_valid_filename(link.name) + '.mp4'

    if output_path.joinpath(filename).exists():
        logger.debug('file {} exists in disk, not downloading'.format(filename))
        return None

    logger.debug('downloading {} to folder {}'.format(filename, str(output_path)))
    return async_download_video(video_link=link.link,
                                folder=str(output_path),
                                filename=filename)


def main():
    if args.use_virtual_display:
        import pyvirtualdisplay

        display = pyvirtualdisplay.Display(visible=0, size=(800, 600))
        display.start()

    scraper = ArtistWorkScraper(fetch_extras=args.fetch_extras, use_firefox=args.use_firefox)
    scraper.login_to_artistworks(username=args.username, password=args.password)

    if args.only_lessons:
        lesson_ids = args.only_lessons
        department_name = 'Misc lessons'
    else:
        department_name = scraper.get_department_name(args.department)
        lesson_ids = scraper.get_all_lesson_ids_for_department(args.department)

    for lesson_id in lesson_ids:
        if lesson_id not in lessons_db:
            lessons_db[lesson_id] = scraper.get_lesson_by_id(lesson_id)

        if args.fetch_masterclasses:
            for masterclass_id in lessons_db[lesson_id].masterclass_ids:
                if masterclass_id not in masterclasses_db:
                    masterclasses_db[masterclass_id] = scraper.get_masterclass_by_id(masterclass_id)

    # start downlaoding
    loop = asyncio.get_event_loop()

    futures = []
    for lesson in lessons_db.values():
        output_path = Path(args.output_dir).joinpath('Paul Gilbert').joinpath(department_name).joinpath(
            get_valid_filename(lesson.name))

        for lesson_link in lesson.links:
            futures.append(download_link(lesson_link, output_path))

        if args.fetch_masterclasses:
            for masterclass_id in lesson.masterclass_ids:
                masterclass = masterclasses_db[masterclass_id]
                for masterclass_link in masterclass.links:
                    output_path = output_path.joinpath(masterclass.name)
                    futures.append(download_link(masterclass_link, output_path))

    f = wait_with_progress(list(filter(None, futures)))
    loop.run_until_complete(f)

    scraper.exit()
