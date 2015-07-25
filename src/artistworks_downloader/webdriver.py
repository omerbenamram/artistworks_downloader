from collections import namedtuple
import contextlib
import re
import time

import logbook
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .constants import ARTISTWORKS_LOGIN, ARTISTWORKS_LESSON_BASE, ARTISTWORKS_DEPARTMENT_BASE, \
    ARTISTWORKS_MASTERCLASS_BASE, LOG_PATH

logger = logbook.Logger(__name__)
logger.handlers.append(logbook.FileHandler(LOG_PATH, bubble=True))
logger.handlers.append(logbook.StderrHandler())


class Lesson(namedtuple('Lesson', field_names=['id', 'name', 'links', 'masterclass_ids'])):
    pass


class Masterclass(namedtuple('Masterclass', field_names=['id', 'name', 'links'])):
    pass


class LessonLink(namedtuple('LessonLink', field_names=['name', 'link'])):
    pass


class ArtistWorkScraper(object):
    def __init__(self, fetch_extras=False, use_firefox=False):
        if use_firefox:
            self.driver = Firefox()
        else:
            self.driver = Chrome()
        self.fetch_extras = fetch_extras

    def login_to_artistworks(self, username, password):
        logger.info('Connecting to artistworks with user {}'.format(username))
        self.driver.get(ARTISTWORKS_LOGIN)
        username_input = self.driver.find_element_by_xpath('//*[@id="edit-name"]')
        username_input.send_keys(username)
        password_input = self.driver.find_element_by_xpath('//*[@id="edit-pass"]')
        password_input.send_keys(password)
        login_button = self.driver.find_element_by_xpath('//*[@id="edit-submit"]')
        login_button.click()
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="blk-artistworks_user-4"]/div/div[2]/div[1]/span')))
        except TimeoutException as t:
            logger.exception(t)
            logger.critical('Failed to login!')

    def get_masterclass_by_id(self, masterclass_id):
        logger.info('grabbing info for masterclass {}'.format(masterclass_id))
        if not self.driver.current_url == (ARTISTWORKS_MASTERCLASS_BASE + str(masterclass_id)):
            self.driver.get(ARTISTWORKS_MASTERCLASS_BASE + str(masterclass_id))

        lesson_name_element = self.driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
        lesson_links = []
        try:
            elements = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'playlist-item')))
        except TimeoutException:
            # for masterclass, i don't care about those without artist response
            return Masterclass(masterclass_id, lesson_name_element.text, lesson_links)

        for element in elements:
            lesson_links.append(LessonLink(element.text, self._get_video_link_for_element(element)))

        return Masterclass(masterclass_id, lesson_name_element.text, lesson_links)

    def get_lesson_by_id(self, lesson_id):
        logger.info('grabbing info for lesson {}'.format(lesson_id))
        if not self.driver.current_url == (ARTISTWORKS_LESSON_BASE + str(lesson_id)):
            self.driver.get(ARTISTWORKS_LESSON_BASE + str(lesson_id))

        lesson_name_element = self.driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
        lesson_links = []
        try:
            elements = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'playlist-item')))
        except TimeoutException:
            elements = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.ID, 'player0_wrapper')))

        for element in elements:
            lesson_links.append(LessonLink(element.text, self._get_video_link_for_element(element)))
            if not self.fetch_extras:
                break

        content = self.driver.page_source
        soup = BeautifulSoup(content)
        masterclasses_ids = list(map(lambda x: re.findall('\d+', x['href'])[0],
                                     soup.find_all('a', href=re.compile('/masterclass/(\d+)'))))

        return Lesson(lesson_id, lesson_name_element.text, lesson_links, masterclasses_ids)

    def _get_video_link_for_element(self, element):
        logger.info('grabbing links for element {}'.format(element))
        element.click()
        # small sleep is still needed for some js to initialize
        i = 0
        link = None
        while i <= 3:
            try:
                time.sleep(5)
                self.driver.execute_script("return jwplayer().stop()")
                link = self.driver.execute_script("return jwplayer().getPlaylistItem()['file']")
            except WebDriverException as e:
                logger.exception(e)
                logger.debug('waiting and retrying')
                i += 1
            break
        if not link:
            raise Exception('Could not find link!')

        logger.info('found link {}'.format(link))
        return link

    def get_department_name(self, department_id):
        if not self.driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
            self.driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))
        department_name_element = self.driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
        return department_name_element.text

    def get_all_lesson_ids_for_department(self, department_id):
        logger.info('grabbing all links for department {}'.format(department_id))
        if not self.driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
            self.driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))

        with contextlib.suppress(TimeoutException):
            # this is somewhat of an improved sleep (sometimes the table is different)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '#media-group-table > table.sticky-enabled.sticky-table')))

        content = self.driver.page_source
        soup = BeautifulSoup(content)
        lesson_ids = map(lambda x: re.findall('\d+', x['href'])[0],
                         soup.find_all('a', href=re.compile('/lesson/(\d+)')))

        return lesson_ids

    def exit(self):
        self.driver.close()
