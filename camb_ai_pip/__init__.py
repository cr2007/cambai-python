import os
import os
import requests
from time import sleep
from typing import Optional, Literal, TypedDict

class APIKeyMissingError(Exception):
    """Exception raised when the API Key is missing."""


class APIError(Exception):
    """Exception raised when an API error occurs. \n
    Mostly when a non-200 status code is returned."""


class DubbingTaskStatus(TypedDict):
    status: Literal["SUCCESS", "PENDING", "TIMEOUT", "ERROR", "PAYMENT_REQUIRED"]
    run_id: Optional[int]


class DubbedRunInfo(TypedDict):
    """
    Represents information about a dubbed run.

    Attributes:
        - video_url (str): The URL of the video.
        - audio_url (str): The URL of the audio.
    """
    video_url: str
    audio_url: str


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


    def get_languages(self, type: Literal["source", "target"], get_languages: bool = False) -> list[dict]:
        url: str = self.create_api_endpoint(f"{type}_languages")
        response: requests.Response = self.session.get(url)

        return response.json()


    def get_all_voices(self) -> list[dict]:
        """Get all voices available in Camb AI."""
        url: str = self.create_api_endpoint("list_voices")
        response: requests.Response = self.session.get(url)
        return response.json()


    ### Dub Example ####

    def get_dubbing_task_status(self, task_id: str) -> DubbingTaskStatus:
        url: str = self.create_api_endpoint(f"end_to_end_dubbing/{task_id}")
        response = self.session.get(url)
        return response.json()


    def get_dubbed_run_info(self, run_id: int) -> DubbedRunInfo:
        url: str = self.create_api_endpoint(f"dubbed_run_info/{run_id}")
        response = self.session.get(url)
        return response.json()


    def start_dubbing(self, *, video_url: str, source_language: int = 1,
                      target_language: int) -> dict:
        url: str = self.create_api_endpoint("end_to_end_dubbing")
        self.session.headers["Content-Type"] = "application/json"

        data: dict = {
            "video_url": video_url,
            "source_language": source_language,
            "target_language": target_language
        }

        response = self.session.post(url, json=data)

        if response.status_code == 200:
            print("Poo Poo Response 200")
            return response.json()
        else:
            print("Big L")
            raise APIError(response.json())


    def dub(self, *, video_url: str, source_language: int = 1, target_language: int,
            polling_interval:int = 2, debug: bool = False):
        task: DubbingTaskStatus
        task_id: str

        print("Starting Dubbing")
        response = self.start_dubbing(video_url=video_url, source_language=source_language,
                                      target_language=target_language)

        print(f"Dubbing Task Started: {response}")

        task_id = response["task_id"]

        while True:
            task = self.get_dubbing_task_status(task_id)
            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")
            if task["status"] == "SUCCESS":
                break
            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(f"Dubbing Issue: {task['status']} for Run ID: {task["run_id"]}")

            sleep(polling_interval)

        task = self.get_dubbing_task_status(task_id)
        if task["run_id"] is None:
            raise APIError("Run ID is None")
        return self.get_dubbed_run_info(task["run_id"])
