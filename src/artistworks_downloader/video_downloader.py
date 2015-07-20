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
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.connector = aiohttp.TCPConnector(share_cookies=True, loop=self.loop)
        self.coros = []
        self.sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    @asyncio.coroutine
    def async_download_video(self, video_link, chunk_size=1024, folder=r'C:\Temp', filename=''):
        with aiohttp.ClientSession(connector=self.connector) as session, (yield from self.sem):
            vid = yield from session.get(video_link)
            if not filename:
                filename = video_link.split('/')[-1]
            with open(os.path.join(folder, filename), 'wb') as fd:
                while True:
                    chunk = yield from vid.content.read(chunk_size)
                    if not chunk:
                        break
                    fd.write(chunk)
        logger.info('Finished downloading file {}'.format(filename))

    @asyncio.coroutine
    def wait_with_progress(self, coros):
        for f in tqdm.tqdm(asyncio.as_completed(coros), total=len(coros)):
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

        logger.debug('downloading {} to folder {}'.format(filename, str(output_folder_path)))
        self.coros.append(self.async_download_video(video_link=link.link,
                                                    folder=str(output_folder_path),
                                                    filename=filename))

    def run(self):
        self.loop.run_until_complete(self.wait_with_progress(list(filter(None, self.coros))))


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
