import os
import asyncio
from pathlib import Path
import re

import aiohttp
import logbook
import tqdm

from .constants import MAX_CONCURRENT_DOWNLOADS, LOG_PATH

logger = logbook.Logger(__name__)
logger.handlers.append(logbook.FileHandler(LOG_PATH, bubble=True))
logger.handlers.append(logbook.StderrHandler())


class AsyncDownloader(object):
    def __init__(self, loop=asyncio.get_event_loop()):
        self.loop = loop
        self.busy = set()
        self.done = {}
        self.tasks = set()

        self.sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    @asyncio.coroutine
    def async_download_video(self, video_url, chunk_size=1024, folder=r'C:\Temp', filename=''):
        with aiohttp.ClientSession(loop=self.loop) as session, (yield from self.sem):
            try:
                vid = yield from session.get(video_url)
                if not filename:
                    filename = video_url.split('/')[-1]
            except Exception as exc:
                logger.exception(exc)
                logger.error('Failure trying to download from {}, going to retry later..'.format(video_url))
                self.done[video_url] = False
                return

            with open(os.path.join(folder, filename), 'wb') as fd:
                while True:
                    try:
                        chunk = yield from vid.content.read(chunk_size)
                    except Exception as exc:
                        logger.exception(exc)
                        logger.error('Failure trying to download from {}, going to retry later..'.format(video_url))
                        self.done[video_url] = False
                    if not chunk:
                        break
                    fd.write(chunk)

            vid.close()

        logger.info('Finished downloading file {}'.format(filename))
        self.done[video_url] = True

    @asyncio.coroutine
    def wait_with_progress(self):
        for f in tqdm.tqdm(asyncio.as_completed(self.tasks), total=len(self.tasks)):
            yield from f

    def download_link(self, link, output_folder_path):
        if not isinstance(output_folder_path, Path):
            output_folder_path = Path(output_folder_path)

        if not output_folder_path.exists():
            os.makedirs(str(output_folder_path))

        filename = get_valid_filename(link.name) + '.mp4'

        if output_folder_path.joinpath(filename).exists():
            logger.debug('file {} exists in disk, not downloading'.format(filename))
            return None

        logger.debug('going to download {} to folder {}'.format(filename, str(output_folder_path)))
        task = asyncio.Task(self.async_download_video(video_url=link.link,
                                                      folder=str(output_folder_path),
                                                      filename=filename))
        task.add_done_callback(self.tasks.remove)
        self.tasks.add(task)

    def run(self):
        self.loop.run_until_complete(self.wait_with_progress())


def get_valid_filename(s):
    """
    Returns the given string converted to a string that can be used for a clean
    filename. Specifically, leading and trailing spaces are removed; other
    spaces are converted to underscores; and anything that is not a unicode
    alphanumeric, dash, underscore, or dot, is removed.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = s.strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)
