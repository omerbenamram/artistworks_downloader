import os

import asyncio
import shelve

import aiohttp
import tqdm

from .constants import MAX_CONCURRENT_DOWNLOADS, DB_PATH

sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
db = shelve.open(DB_PATH)


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


@asyncio.coroutine
def wait_with_progress(coros):
    for f in tqdm.tqdm(asyncio.as_completed(coros), total=len(coros)):
        yield from f
