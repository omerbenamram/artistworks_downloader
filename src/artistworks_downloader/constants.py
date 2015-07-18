from pathlib import Path

ARTISTWORKS_LOGIN = 'https://secure.artistworks.com/awentry'
ARTISTWORKS_LESSON_BASE = 'http://artistworks.com/lesson/'
ARTISTWORKS_DEPARTMENT_BASE = 'http://artistworks.com/media-department/'
ARTISTWORKS_MASTERCLASS_BASE = 'http://artistworks.com/masterclass/'

DEFAULT_OUTPUT_DIRECTORY = r'C:\Temp\ArtistWorks'
MAX_CONCURRENT_DOWNLOADS = 5

LESSONS_DB_PATH = str(Path(DEFAULT_OUTPUT_DIRECTORY).joinpath('lessons.db'))
MASTERCLASSES_DB_PATH = str(Path(DEFAULT_OUTPUT_DIRECTORY).joinpath('masterclasses.db'))
