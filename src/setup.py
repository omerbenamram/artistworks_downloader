from setuptools import setup, find_packages

setup(
    name='artistworks_downloader',
    packages=find_packages(),
    url='',
    license='',
    author='Omer',
    author_email='omerbenamram@gmail.com',
    description='a script to grab videos from artistworks',
    entry_points={
        'console_scripts': [
            'artistworks_downloader = main:main',
        ],
    }, requires=['selenium', 'logbook', 'aiohttp', 'tqdm']
)
