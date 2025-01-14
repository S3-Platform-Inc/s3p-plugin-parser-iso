import datetime
import time
import dateparser
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class ISO(S3PParserBase):
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'iso'

    def __init__(self, urls: tuple | list, refer: S3PRefer, web_driver: WebDriver, max_count_documents: int = None,
                 last_document: S3PDocument = None):
        super().__init__(refer, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        self.URLS = urls

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter")

        for url in self.URLS:
            self._driver.get(url)
            self._wait.until(ec.presence_of_element_located((By.TAG_NAME, 'tbody')))
            category = self._driver.find_element(By.CLASS_NAME, 'heading-condensed').text.replace('\n', ' ')
            docs = self._driver.find_elements(By.XPATH, "//tbody/tr[contains(@ng-show, 'pChecked')]")
            for doc in docs:
                title = doc.find_element(By.CLASS_NAME, 'clearfix').text.replace('\n', ' ')
                standard_link = (doc.find_element(By.CLASS_NAME, 'clearfix')
                                 .find_element(By.TAG_NAME, 'a').get_attribute('href'))
                stage_short = doc.find_element(By.XPATH, ".//td[contains(@data-title, 'Stage')]").text
                tech_committee_short = doc.find_element(By.XPATH, ".//td[contains(@data-title, 'TC')]").text

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])

                self._driver.get(standard_link)
                self._wait.until(ec.presence_of_element_located((By.TAG_NAME, 'nav')))

                self.logger.debug(f'Enter {standard_link}')

                heading = self._driver.find_element(By.XPATH, "//nav[contains(@class, 'heading-condensed')]")

                # doc_ref = heading.find_element(By.TAG_NAME, 'h1').text
                # topic = heading.find_element(By.TAG_NAME, 'h2').text

                # try:
                #     subtopic = heading.find_element(By.TAG_NAME, 'h3').text
                # except:
                #     subtopic = None

                # try:
                #     part = heading.find_element(By.TAG_NAME, 'h4').text
                # except:
                #     part = None

                try:
                    abstract = self._driver.find_element(By.XPATH, "//div[contains(@itemprop,'description')]").text
                except:
                    abstract = None

                try:
                    status = self._driver.find_element(By.XPATH, "//a[contains(@title,'Life cycle')]").text
                except:
                    status = None

                pub_date = dateparser.parse(self._driver.find_element(
                    By.XPATH, "//div[@id = 'publicationDate']/span").text)

                web_link = self._driver.find_element(By.XPATH, "//a[contains(text(),'Read sample')]").get_attribute(
                    'href')

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[2])

                self._driver.get(web_link)
                self._wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'sts-standard')))

                text_content = self._driver.find_element(By.XPATH, "//div[contains(@class, 'sts-standard')]").text

                other_data = {
                    # 'doc_ref': doc_ref,
                    # 'topic': topic,
                    # 'subtopic': subtopic,
                    # 'part': part,
                    'category': category,
                    'category_link': url,
                    'status': status,
                    'stage': stage_short,
                    'tech_committee': tech_committee_short,
                    'standard_page': standard_link
                }

                doc = S3PDocument(
                    id=None,
                    title=title,
                    abstract=abstract,
                    text=text_content,
                    link=web_link,
                    storage=None,
                    other=other_data,
                    published=pub_date,
                    loaded=datetime.datetime.now(),
                )

                self._find(doc)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[1])
                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])

        # ---
        # ========================================
        ...
