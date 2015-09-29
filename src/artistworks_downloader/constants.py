import os
from pathlib import Path

ARTISTWORKS_LOGIN = 'https://secure.artistworks.com/awentry'
ARTISTWORKS_LESSON_BASE = 'http://artistworks.com/lesson/'
ARTISTWORKS_DEPARTMENT_BASE = 'http://artistworks.com/media-department/'
ARTISTWORKS_MASTERCLASS_BASE = 'http://artistworks.com/masterclass/'

DEFAULT_OUTPUT_DIRECTORY = str(Path(os.path.expanduser('~')).joinpath('ArtistWorks'))

MAX_CONCURRENT_DOWNLOADS = 5
MAX_RETRIES = 5
RETRY_DURATION = 60

if os.name == 'nt':
    LOG_PATH = os.path.join(os.path.expandvars('%LOCALAPPDATA%'), 'temp', 'artistworks_downloader.log')
else:
    LOG_PATH = os.path.join(os.path.expandvars('/var'), 'log', 'artistworks_downloader.log')
