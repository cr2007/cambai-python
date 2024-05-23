import os
import requests
import json
from urllib.parse import urljoin
from camb_ai_pip import APIKeyMissingError
from typing import Optional, Literal

LanguageTypes = Literal["source", "target"]

class CambAI(object):
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
    ) -> None:
        if api_key is None:
            api_key = os.getenv("CAMB_API_KEY")
        if api_key is None:
            raise APIKeyMissingError(
                "All methods require a Camb AI API key. See "
                "https://studio.camb.ai "
                "for how to retrieve an API key from Camb AI"
            )

        self.CAMB_URL: str = "https://client.camb.ai/apis/"

        self.session: requests.Session = requests.Session()
        self.session.headers = {"x-api-key": api_key}

    def create_api_endpoint(self, endpoint: str) -> str:
        return self.CAMB_URL + endpoint

    def get_languages(self, type: LanguageTypes) -> list[dict]:
        url: str = self.create_api_endpoint(f"{type}_languages")
        response: requests.Response = self.session.get(url)
        return response.json()

    # def get_all_voices()


def run_test():
    from dotenv import load_dotenv
    load_dotenv()
    camb = CambAI()

    source_languages = camb.get_languages("source")
    print(source_languages)
