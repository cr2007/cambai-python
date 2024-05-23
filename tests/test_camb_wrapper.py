import os
from pytest import fixture
from dotenv import load_dotenv
from camb_ai_pip.camb_client import CambAI
import vcr

load_dotenv()


def test_get_source_languages():
    """Tests and API call to retrieve all source languages."""
    api_key = os.getenv("CAMB_API_KEY")
    camb_instance = CambAI(api_key=api_key)
    source_languages = camb_instance.get_languages("source")
    assert len(source_languages) > 0
    assert sorted(source_languages[0].keys(), key=len, reverse=False) == ["id", "language", "short_name"]
    assert source_languages[0]["language"] == "english (united states)"
    assert source_languages[2]["language"] == "amharic (ethiopia)"


def test_get_target_languages():
    """Tests and API call to retrieve all source languages."""
    api_key = os.getenv("CAMB_API_KEY")
    camb_instance = CambAI(api_key=api_key)
    source_languages = camb_instance.get_languages("target")
    assert len(source_languages) > 0
    assert sorted(source_languages[0].keys(),
                  key=len,
                  reverse=False) == ["id", "language", "short_name"]
    assert source_languages[0]["language"] == "english (united states)"
    assert source_languages[2]["language"] == "amharic (ethiopia)"
