from collections import namedtuple
import re
import time

import logbook

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .constants import ARTISTWORKS_LOGIN, ARTISTWORKS_LESSON_BASE, ARTISTWORKS_DEPARTMENT_BASE

logger = logbook.Logger(__name__)

Lesson = namedtuple(typename='lesson', field_names=['id', 'name'])


class ArtistWorkScraper(object):
    def __init__(self):
        self.driver = Chrome()

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

    def get_lesson_by_id(self, lesson_id):
        logger.info('grabbing info for lesson {}'.format(lesson_id))
        if not self.driver.current_url == (ARTISTWORKS_LESSON_BASE + str(lesson_id)):
            self.driver.get(ARTISTWORKS_LESSON_BASE + str(lesson_id))

        lesson_name_element = self.driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
        return Lesson(lesson_id, lesson_name_element.text)

    def get_video_link_for_lesson(self, lesson):
        logger.info('grabbing link for lesson {}'.format(lesson.id))
        if not self.driver.current_url == (ARTISTWORKS_LESSON_BASE + str(lesson.id)):
            self.driver.get(ARTISTWORKS_LESSON_BASE + str(lesson.id))

        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#player0')))
        # small sleep is still needed for some js to initialize
        i = 0
        link = None
        while i < 3:
            try:
                time.sleep(5)
                link = self.driver.execute_script("return jwplayer().getPlaylistItem()['file']")
            except WebDriverException as e:
                logger.exception(e)
                logger.debug('waiting and retrying')
                time.sleep(5)
                i += 1

            break
        if not link:
            raise Exception('Could not find link for lesson id {}'.format(lesson.id))

        logger.info('found link {}'.format(link))
        return link

    def get_department_name(self, department_id):
        if not self.driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
            self.driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))
        department_name_element = self.driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
        return department_name_element.text

    def get_all_lessons_for_department(self, department_id):
        """
        :param department_id:
        :return: a list of tuples containing lesson_id, lesson_name
        :rtype: list(lesson)
        """
        logger.info('grabbing all links for department {}'.format(department_id))
        if not self.driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
            self.driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#media-group-table > table.sticky-enabled.sticky-table')))
        content = self.driver.page_source
        soup = BeautifulSoup(content)
        links = list(map(lambda x: Lesson(id=re.findall('\d+', x['href'])[0], name=x.text),
                         soup.find_all('a', href=re.compile('/lesson/(\d+)'))))
        logger.info('found {} links!'.format(len(links)))
        return links

    def exit(self):
        self.driver.close()
