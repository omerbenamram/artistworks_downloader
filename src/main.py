import argparse
import asyncio
import os
from pathlib import Path

from downloader.constants import DEFAULT_OUTPUT_DIRECTORY
from downloader.webdriver import ArtistWorkScraper
from downloader.video_downloader import async_download_video, wait_with_progress, get_valid_filename

parser = argparse.ArgumentParser(description='Grabs videos from artistworks')
parser.add_argument('--username', type=str, required=True,
                    help='Username to connect to artistworks')
parser.add_argument('--password', type=str, required=True,
                    help='Password to connect to artistworks')
parser.add_argument('--output_dir', type=str, nargs='?', default=DEFAULT_OUTPUT_DIRECTORY,
                    help='specify output directory')

links_group = parser.add_mutually_exclusive_group(required=True)
links_group.add_argument('--department', type=int, nargs=1,
                         help='Department number to be scraped')
links_group.add_argument('--only_lessons', type=str, nargs='*',
                         help='download only specified lessons')


def main():
    args = parser.parse_args()
    scraper = ArtistWorkScraper()
    scraper.login_to_artistworks(username=args.username, password=args.password)

    if args.only_lessons:
        department_name = 'Misc lessons'
        lessons = []
        links = {}
        for lesson_id in args.only_lessons:
            lesson = scraper.get_lesson_by_id(lesson_id)
            lessons.append(lesson)
            links[lesson.id] = scraper.get_video_link_for_lesson(lesson)

    else:
        lessons = scraper.get_all_lessons_for_department(args.department)
        department_name = scraper.get_department_name(args.department)
        links = {lesson.id: scraper.get_video_link_for_lesson(lesson) for lesson in lessons}

    # start downlaoding
    loop = asyncio.get_event_loop()

    futures = []
    for lesson in lessons:
        output_path = Path(args.output_dir).joinpath('Paul Gilbert').joinpath(department_name).joinpath(
            get_valid_filename(lesson.name))

        if not output_path.exists():
            os.makedirs(str(output_path))

        futures.append(async_download_video(video_link=links[lesson.id],
                                            folder=str(output_path),
                                            filename=(get_valid_filename(lesson.name) + '.mp4')))

    f = wait_with_progress(futures)
    loop.run_until_complete(f)

    scraper.exit()
