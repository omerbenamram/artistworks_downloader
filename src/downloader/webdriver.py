from collections import namedtuple
import re
import time

import logbook

from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .constants import ARTISTWORKS_LOGIN, ARTISTWORKS_LESSON_BASE, ARTISTWORKS_DEPARTMENT_BASE

driver = Chrome()
logger = logbook.Logger(__name__)

lesson = namedtuple(typename='lesson', field_names=['id', 'name'])


def initialize_webdriver(browser=Chrome):
    """
    :param browser: a selenium webdriver class
    :return: webdriver instance
    """
    return browser()


def login_to_artistworks(username, password):
    logger.info('Connection to artistworks with user {}'.format(username))
    driver.get(ARTISTWORKS_LOGIN)
    username_input = driver.find_element_by_xpath('//*[@id="edit-name"]')
    username_input.send_keys(username)
    password_input = driver.find_element_by_xpath('//*[@id="edit-pass"]')
    password_input.send_keys(password)
    login_button = driver.find_element_by_xpath('//*[@id="edit-submit"]')
    login_button.click()


def get_lesson_video_link_by_id(lesson_id):
    logger.info('grabbing link for lesson {}'.format(lesson_id))
    driver.get(ARTISTWORKS_LESSON_BASE + str(lesson_id))
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#player0')))
    # small sleep is still needed for some js to initialize
    time.sleep(1)
    link = driver.execute_script("return jwplayer().getPlaylistItem()['file']")
    logger.info('found link {}'.format(link))
    return link


def get_department_name(department_id):
    if not driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
        driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))
    element = driver.find_element_by_xpath('//*[@id="tabs-wrapper"]/h2')
    return element.text


def get_all_links_for_department(department_id):
    """
    :param department_id:
    :return: a list of tuples containing lesson_id, lesson_name
    :rtype: list(lesson)
    """
    logger.info('grabbing all links for department {}'.format(department_id))
    if not driver.current_url == (ARTISTWORKS_DEPARTMENT_BASE + str(department_id)):
        driver.get(ARTISTWORKS_DEPARTMENT_BASE + str(department_id))

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#media-group-table > table.sticky-enabled.sticky-table')))
    content = driver.page_source
    soup = BeautifulSoup(content)
    links = list(map(lambda x: lesson(id=re.findall('\d+', x['href'])[0], name=x.text),
                     soup.find_all('a', href=re.compile('/lesson/(\d+)'))))
    logger.info('found {} links!'.format(len(links)))
    return links
