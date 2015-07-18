import os

import asyncio
import re

import aiohttp
import tqdm

from .constants import MAX_CONCURRENT_DOWNLOADS

sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)


@asyncio.coroutine
def async_download_video(video_link, chunk_size=1024, folder=r'C:\Temp', filename=''):
    with aiohttp.ClientSession() as session, (yield from sem):
        vid = yield from session.get(video_link)
        if not filename:
            filename = video_link.split('/')[-1]
        with open(os.path.join(folder, filename), 'wb') as fd:
            while True:
                chunk = yield from vid.content.read(chunk_size)
                if not chunk:
                    break
                fd.write(chunk)


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


@asyncio.coroutine
def wait_with_progress(coros):
    for f in tqdm.tqdm(asyncio.as_completed(coros), total=len(coros)):
        yield from f
