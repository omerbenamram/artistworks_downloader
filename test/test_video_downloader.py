import random
import py

from artistworks_downloader.video_downloader import AsyncDownloader
from artistworks_downloader.webdriver import LessonLink

Path = py.path.local

args = [(LessonLink(name='Fast Descending Pentatonic Pattern 1', link='http://pgsgcdn.05.awimedia.net/media/0/2/8/227_34028_57213_23fastdescendpentatonic_awlf_114.mp4'),
         r'C:\Users\Omer\ArtistWorks\Paul Gilbert\Misc lessons\Fast_Descending_Pentatonic_Pattern_1'),
        (LessonLink(name='fast descending pentatonic 1', link='http://pgsgcdn.05.awimedia.net/media/7/5/0/52186_100750_134474_Video3_112.mp4'),
         r'C:\Users\Omer\ArtistWorks\Paul Gilbert\Misc lessons\Fast_Descending_Pentatonic_Pattern_1\blaborde - 16th Note Groove Lock and Endings')
        ,(LessonLink(name="Paul's Response", link='http://pgsgcdn.05.awimedia.net/media/4/0/7/9182_101407_135131_00047_112.mp4'),
          r'C:\Users\Omer\ArtistWorks\Paul Gilbert\Misc lessons\Fast_Descending_Pentatonic_Pattern_1\blaborde - 16th Note Groove Lock and Endings')]

links = [LessonLink(name='Fast Descending Pentatonic Pattern 1', link='http://pgsgcdn.05.awimedia.net/media/0/2/8/227_34028_57213_23fastdescendpentatonic_awlf_114.mp4'),
        LessonLink(name='fast descending pentatonic 1', link='http://pgsgcdn.05.awimedia.net/media/7/5/0/52186_100750_134474_Video3_112.mp4'),
        LessonLink(name="Paul's Response", link='http://pgsgcdn.05.awimedia.net/media/4/0/7/9182_101407_135131_00047_112.mp4')]


def test_downloads_single_file_correctly(tmpdir, event_loop):
    downloader = AsyncDownloader(loop=event_loop)
    path = str(Path(tmpdir).join(str(random.randint(1, 10000)) + '.mp4'))
    downloader.download_link(links[1], path)
    downloader.run()

