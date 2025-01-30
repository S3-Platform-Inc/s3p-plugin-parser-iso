import time
from typing import Iterator
import dateutil
import feedparser

from s3p_sdk.exceptions.parser import S3PPluginParserOutOfRestrictionException, S3PPluginParserFinish
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions
from s3p_sdk.types.plugin_restrictions import FROM_DATE
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class ISO(S3PParserBase):
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.

    :self.feeds: list[str, ...]
    Список потоков ISO для
    1. ISO 03.060 Finances. Banking. Monetary systems. Insurance Including personal financial planning https://www.iso.org/ics/03.060/x/
    https://www.iso.org/contents/data/ics/03.060.rss

    2. ISO 35.020 Information technology (IT) in general Including general aspects of IT equipment https://www.iso.org/ics/35.020/x/
    https://www.iso.org/contents/data/ics/35.020.rss

    3. ISO 35.240.15 Identification cards. Chip cards. Biometrics Including application of cards for banking, trade, telecommunications, transport, etc. https://www.iso.org/ics/35.240.15/x/
    https://www.iso.org/contents/data/ics/35.240.15.rss

    4. ISO 35.240.40 IT applications in banking Including automatic banking facilities https://www.iso.org/ics/35.240.40/x/
    https://www.iso.org/contents/data/ics/35.240.40.rss

    """

    def __init__(self,
                 refer: S3PRefer,
                 plugin: S3PPlugin,
                 restrictions: S3PPluginRestrictions,
                 web_driver: WebDriver,
                 feeds: tuple | list
                 ):
        super().__init__(refer, plugin, restrictions)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        self.feeds = feeds

    def _parse(self) -> None:
        if isinstance(self._restriction.maximum_materials, int) and self._restriction.maximum_materials // len(self.feeds) >= 4:
            number = self._restriction.maximum_materials // len(self.feeds) + 1
        else:
            number = self._restriction.maximum_materials

        for feed in self.feeds:
            for document in self._slices(
                self._feed(
                    feed
                ),
                number
            ):
                if document.link.endswith('.html'):
                    # visit webpage
                    self._driver.get(document.link)
                    time.sleep(2)

                    # Abstract
                    try:
                        abstract = self._driver.find_element(By.CSS_SELECTOR, 'div[itemprop="description"]')
                        document.abstract = abstract.text
                    except:
                        pass

                    # Other Data
                    try:
                        document.other['general'] = {}
                        status = self._driver.find_element(By.CSS_SELECTOR, 'div#publicationStatus > span')
                        document.other['general']['status'] = status.text

                        # steps
                        steps = self._driver.find_elements(By.CSS_SELECTOR, 'ul.steps > li')
                        for step in steps:
                            try:
                                document.other.get('general')['stage'] = step.find_element(By.CSS_SELECTOR, 'a.current-stage > strong').text
                            except: ...
                    except: ...

                try:
                    self._find(document)
                except S3PPluginParserOutOfRestrictionException as e:
                    if e.restriction == FROM_DATE:
                        break



    def _slices(self, feed: Iterator[S3PDocument], number: int | None = None) -> Iterator[S3PDocument]:
        for current, element in enumerate(feed):
            if number is not None and current >= number:
                break
            yield element

    def _feed(self, url: str) -> Iterator[S3PDocument]:
        # Parse the ECB RSS feed
        feed = feedparser.parse(url)

        # Iterate through feed entries
        for entry in feed.entries:
            parsed_date = dateutil.parser.parse(entry.published)

            yield S3PDocument(
                None,
                entry.title,
                None,
                None,
                entry.link,
                None,
                {
                    'summary': entry.description if 'summary' in entry else None,
                },
                parsed_date.replace(tzinfo=None),
                None,
            )
