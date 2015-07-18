import argparse
import asyncio
from pathlib import Path

from downloader.constants import DEFAULT_OUTPUT_DIRECTORY
from downloader.webdriver import login_to_artistworks, get_all_links_for_department, get_lesson_video_link_by_id, \
    get_department_name
from downloader.video_downloader import async_download_video, wait_with_progress

parser = argparse.ArgumentParser(description='Grabs videos from artistworks')
parser.add_argument('department', type=int, required=True,
                    help='Department number to be scraped')
parser.add_argument('username', type=str, required=True,
                    help='Username to connect to artistworks')
parser.add_argument('password', type=str, required=True,
                    help='Password to connect to artistworks')
parser.add_argument('output_dir', type=str, nargs='?', default=DEFAULT_OUTPUT_DIRECTORY,
                    help='specify output directory')


def main():
    args = parser.parse_args()
    
    login_to_artistworks(username=args.username, password=args.password)
    department_name = get_department_name(args.department)
    lessons = get_all_links_for_department(args.department)
    links = {lesson.id: get_lesson_video_link_by_id(lesson.id) for lesson in lessons}

    # start downlaoding
    loop = asyncio.get_event_loop()

    futures = []
    for lesson in lessons:
        output_path = Path(args.output_dir).joinpath('Paul Gilbert').joinpath(department_name).joinpath(lesson.name)
        futures.extend(async_download_video(video_link=links[lesson.id],
                                            folder=str(output_path),
                                            filename=(lesson.name + '.mp4')))

    f = wait_with_progress(futures)
    loop.run_until_complete(f)
