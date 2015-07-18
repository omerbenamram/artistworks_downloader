import argparse
import asyncio
import os
from pathlib import Path

import logbook

from artistworks_downloader.constants import DEFAULT_OUTPUT_DIRECTORY
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

links_group = parser.add_mutually_exclusive_group(required=True)
links_group.add_argument('--department', type=int, nargs=1,
                         help='Department number to be scraped')
links_group.add_argument('--only_lessons', type=str, nargs='*',
                         help='download only specified lessons')

logger = logbook.Logger(__name__)


def main():
    args = parser.parse_args()
    scraper = ArtistWorkScraper(fetch_extras=args.fetch_extras)
    scraper.login_to_artistworks(username=args.username, password=args.password)

    if args.only_lessons:
        department_name = 'Misc lessons'
        lessons = [scraper.get_lesson_by_id(lesson_id) for lesson_id in args.only_lessons]

    else:
        department_name = scraper.get_department_name(args.department)
        lessons = scraper.get_all_lessons_for_department(args.department)

    masterclasses = {}
    if args.fetch_masterclasses:
        for lesson in lessons:
            for masterclass_id in lesson.masterclass_ids:
                masterclasses[masterclass_id] = scraper.get_masterclass_by_id(masterclass_id)

    # start downlaoding
    loop = asyncio.get_event_loop()

    futures = []
    for lesson in lessons:
        output_path = Path(args.output_dir).joinpath('Paul Gilbert').joinpath(department_name).joinpath(
            get_valid_filename(lesson.name))

        if not output_path.exists():
            os.makedirs(str(output_path))

        for lesson_item in lesson.links.items():
            filename = get_valid_filename(lesson_item[0]) + '.mp4'
            logger.debug('downloading {} to folder {}'.format(filename, str(output_path)))
            futures.append(async_download_video(video_link=lesson_item[1],
                                                folder=str(output_path),
                                                filename=filename))
        if args.fetch_masterclasses:
            for masterclass in masterclasses.values():
                output_path = output_path.joinpath(masterclass.name)
                if not output_path.exists():
                    os.makedirs(str(output_path))
                    
                for masterclass_links_dict in masterclass.links.items():
                    filename = get_valid_filename(masterclass_links_dict[0]) + '.mp4'
                    logger.debug('downloading {} to folder {}'.format(filename, str(output_path)))
                    futures.append(async_download_video(video_link=masterclass_links_dict[1],
                                                        folder=str(output_path),
                                                        filename=filename))

    f = wait_with_progress(futures)
    loop.run_until_complete(f)

    scraper.exit()
