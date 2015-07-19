import os
from pathlib import Path

ARTISTWORKS_LOGIN = 'https://secure.artistworks.com/awentry'
ARTISTWORKS_LESSON_BASE = 'http://artistworks.com/lesson/'
ARTISTWORKS_DEPARTMENT_BASE = 'http://artistworks.com/media-department/'
ARTISTWORKS_MASTERCLASS_BASE = 'http://artistworks.com/masterclass/'

DEFAULT_OUTPUT_DIRECTORY = Path(os.path.expanduser('~')).joinpath('ArtistWorks')

MAX_CONCURRENT_DOWNLOADS = 5

LOG_PATH = Path(__file__).joinpath('artistwork_downloader.log')
