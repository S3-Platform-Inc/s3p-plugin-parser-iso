from typing import Type

import pytest

# TODO: Указать путь до класса плагина
from src.s3p_plugin_parser_iso.iso import ISO as imported_payload_class


@pytest.fixture(scope="module")
def fix_plugin_class() -> Type[imported_payload_class]:
    return imported_payload_class
