import os
from pathlib import Path

ARTISTWORKS_LOGIN = 'https://secure.artistworks.com/awentry'
ARTISTWORKS_LESSON_BASE = 'http://artistworks.com/lesson/'
ARTISTWORKS_DEPARTMENT_BASE = 'http://artistworks.com/media-department/'
ARTISTWORKS_MASTERCLASS_BASE = 'http://artistworks.com/masterclass/'

DEFAULT_OUTPUT_DIRECTORY = str(Path(os.path.expanduser('~')).joinpath('ArtistWorks'))

MAX_CONCURRENT_DOWNLOADS = 5

LOG_PATH = str(Path(__file__).parent.joinpath('artistwork_downloader.log'))
