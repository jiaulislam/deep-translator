"""
pons translator API
"""
from bs4 import BeautifulSoup
import requests

from .validate import validate_input, is_empty
from .constants import BASE_URLS, PONS_CODES_TO_LANGUAGES
from .exceptions import (
                        TranslationNotFound,
                        NotValidPayload,
                        ElementNotFoundInGetRequest,
                        RequestError,
                        TooManyRequests)
from .base import BaseTranslator
from requests.utils import requote_uri


class PonsTranslator(BaseTranslator):
    """
    class that uses PONS translator to translate words
    """

    def __init__(self, source, target="en", proxies=None, **kwargs):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        self.proxies = proxies
        super().__init__(base_url=BASE_URLS.get("PONS"),
                         languages=PONS_CODES_TO_LANGUAGES,
                         source=source,
                         target=target,
                         payload_key=None,
                         element_tag='div',
                         element_query={"class": "target"},
                         **kwargs
                         )

    def translate(self, word, return_all=False, **kwargs):
        """
        function that uses PONS to translate a word
        @param word: word to translate
        @type word: str
        @param return_all: set to True to return all synonym of the translated word
        @type return_all: bool
        @return: str: translated word
        """
        if validate_input(word, max_chars=50):
            if self._same_source_target() or is_empty(word):
                return word
            url = "{}{}-{}/{}".format(self._base_url, self._source, self._target, word)
            url = requote_uri(url)
            response = requests.get(url, proxies=self.proxies)

            if response.status_code == 429:
                raise TooManyRequests()

            if response.status_code != 200:
                raise RequestError()

            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.findAll(self._element_tag, self._element_query)

            if not elements:
                raise ElementNotFoundInGetRequest(word)

            filtered_elements = []
            for el in elements:
                temp = ''
                for e in el.findAll('a'):
                    temp += e.get_text() + ' '
                filtered_elements.append(temp)

            if not filtered_elements:
                raise ElementNotFoundInGetRequest(word)

            word_list = [word for word in filtered_elements if word and len(word) > 1]

            if not word_list:
                raise TranslationNotFound(word)

            return word_list if return_all else word_list[0]

    def translate_words(self, words, **kwargs):
        """
        translate a batch of words together by providing them in a list
        @param words: list of words you want to translate
        @param kwargs: additional args
        @return: list of translated words
        """
        if not words:
            raise NotValidPayload(words)

        translated_words = []
        for word in words:
            translated_words.append(self.translate(word=word, **kwargs))
        return translated_words

