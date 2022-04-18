import logging
from typing import Optional, Union, Any, Dict

import papis.config
import papis.plugin
import papis.document
from papis.document import Document


FormatDocType = Union[Document, Dict[str, Any]]
logger = logging.getLogger("format")
_FORMATER = None  # type: Optional[Formater]


class InvalidFormatterValue(Exception):
    pass


class Formater:
    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Dict[str, Any] = {}) -> str:
        """
        :param fmt: Python-like format string.
        :type  fmt: str
        :param doc: Papis document
        :type  doc: FormatDocType
        :param doc_key: Name of the document in the format string
        :type  doc: str
        :param additional: Additional named keys available to the format string
        :returns: Formated string
        :rtype: str
        """
        ...


class PythonFormater(Formater):
    """Construct a string using a pythonic format string and a document.
    You can activate this formatter by setting ``formater = python``.
    """
    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Dict[str, Any] = {}) -> str:
        doc_name = doc_key or papis.config.getstring("format-doc-name")
        fdoc = Document()
        fdoc.update(doc)
        try:
            return fmt.format(**{doc_name: fdoc}, **additional)
        except Exception as exception:
            return str(exception)


class Jinja2Formater(Formater):
    """Construct a Jinja2 formated string.
    You can activate this formatter by setting ``formater = jinja2``.
    """

    def __init__(self) -> None:
        try:
            import jinja2
        except ImportError:
            logger.exception("""
            You're trying to format strings using jinja2
            Jinja2 is not installed by default, so just install it
                pip3 install jinja2
            """)
        else:
            self.jinja2 = jinja2

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Dict[str, Any] = {}) -> str:
        doc_name = doc_key or papis.config.getstring("format-doc-name")
        try:
            return str(self.jinja2
                           .Template(fmt)
                           .render(**{doc_name: doc}, **additional))
        except Exception as exception:
            return str(exception)


class CustomFormater(Formater):
    """Provides zotero better-bibtex-like keys.
    """
    SKIP_WORDS = set([
        "about", "above", "across", "afore", "after", "against", "al",
        "along", "alongside", "amid", "amidst", "among", "amongst", "anenst",
        "apropos", "apud", "around", "as", "aside", "astride", "at",
        "athwart", "atop", "barring", "before", "behind", "below", "beneath",
        "beside", "besides", "between", "beyond", "but", "by", "circa",
        "despite", "down", "during", "et", "except", "for", "forenenst",
        "from", "given", "in", "inside", "into", "lest", "like", "modulo",
        "near", "next", "notwithstanding", "of", "off", "on", "onto", "out",
        "over", "per", "plus", "pro", "qua", "sans", "since", "than",
        "through", " thru", "throughout", "thruout", "till", "to", "toward",
        "towards", "under", "underneath", "until", "unto", "up", "upon",
        "versus", "vs.", "v.", "vs", "v", "via", "vis-à-vis", "with",
        "within", "without", "according to", "ahead of", "apart from",
        "as for", "as of", "as per", "as regards", "aside from", "back to",
        "because of", "close to", "due to", "except for", "far from",
        "inside of", "instead of", "near to", "next to", "on to", "out from",
        "out of", "outside of", "prior to", "pursuant to", "rather than",
        "regardless of", "such as", "that of", "up to", "where as", "or",
        "yet", "so", "for", "and", "nor", "a", "an", "the", "de", "d'",
        "von", "van", "c", "ca",
    ])

    def format(self,
               fmt: str,
               doc: FormatDocType,
               doc_key: str = "",
               additional: Dict[str, Any] = {}) -> str:
        if fmt == 'custom_ref':
            author = re.sub('[^a-z]+', '', doc['author_list'][0]['family'].lower())
            year = doc['year'][-2:]
            title = re.sub('-', ' ', doc['title'].lower())
            title = re.sub('[^0-9a-z ]+', '', title)
            title = list(map(str.capitalize, filter(
                lambda word: word and word not in SKIP_WORDS,
                title.split())))
            title = ''.join(title[:4])
            return f'{author}{year}_{title}'
        else:
            return PythonFormater().format(fmt, doc, doc_key, additional)


def _extension_name() -> str:
    return "papis.format"


def get_formater() -> Formater:
    """Get the formatter named 'name' declared as a plugin"""
    global _FORMATER
    if _FORMATER is None:
        name = papis.config.getstring("formater")
        try:
            _FORMATER = papis.plugin.get_extension_manager(
                _extension_name())[name].plugin()
        except KeyError:
            logger.error("Invalid formatter: %s", name)
            raise InvalidFormatterValue(
                "Registered formatters are: %s",
                papis.plugin.get_available_entrypoints(_extension_name()))
        logger.debug("Getting %s", name)

    return _FORMATER


def format(fmt: str,
           doc: FormatDocType,
           doc_key: str = "",
           additional: Dict[str, Any] = {}) -> str:
    formater = get_formater()
    return formater.format(fmt, doc, doc_key=doc_key, additional=additional)
