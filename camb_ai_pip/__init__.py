import os
import requests
from time import sleep
from typing import Optional, Literal, TypedDict

class APIKeyMissingError(Exception):
    """Exception raised when the API Key is missing."""


class APIError(Exception):
    """Exception raised when an API error occurs. \n
    Mostly when a non-200 status code is returned."""

class LanguageOptionsDict(TypedDict):
    """
    Represents a dictionary containing language options.

    Attributes:
        id (int): The ID of the language option.
        language (str): The name of the language.
        short_name (str): The short name of the language.
    """
    id: int
    language: str
    short_name: str


class DubbingTaskStatus(TypedDict):
    """
    A TypedDict representing the status of a dubbing task.

    Attributes:
        - status (Literal["SUCCESS", "PENDING", "TIMEOUT", "ERROR", "PAYMENT_REQUIRED"]):
            The status of the dubbing task. It can be one of the following:
            - "SUCCESS": The task completed successfully.\n
            - "PENDING": The task is still in progress.\n
            - "TIMEOUT": The task timed out before completion.\n
            - "ERROR": An error occurred during the task.\n
            - "PAYMENT_REQUIRED": Payment is required to complete the task.\n
        - run_id (Optional[int]): The unique identifier for the task run. It can be None if the task has not started yet.
    """
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

# --------------------------------------------------------------------------------------------------

class CambAI(object):
    """
    A Python client for interacting with the Camb AI API.

    This class provides methods for various operations including retrieving languages and voices,
    starting the dubbing process for a video, checking the status of a dubbing task, and retrieving
    dubbed run information.

    Attributes:
        CAMB_URL (str): The base URL for the Camb AI API.
        session (requests.Session): The session used for API requests.

    Raises:
        APIKeyMissingError: If the API key is not provided during initialization.
        HTTPError: If a request to the API fails.
        APIError: If there is an issue with the dubbing process.
    """

    def __init__(self, *, api_key: Optional[str] = None) -> None:
        # If no API key is provided, try to get it from the environment variables
        if api_key is None:
            api_key = os.getenv("CAMB_API_KEY")

        # If the API key is still None, raise an error
        if api_key is None:
            raise APIKeyMissingError(
                "All methods require a Camb AI API key. See "
                "https://studio.camb.ai "
                "for how to retrieve an API key from Camb AI"
            )

        # Set the base URL for the Camb AI API
        self.CAMB_URL: str = "https://client.camb.ai/apis/"

        # Create a new session for making requests
        self.session: requests.Session = requests.Session()

        # Set the API key in the session headers
        self.session.headers = {"x-api-key": api_key}


    def create_api_endpoint(self, endpoint: str) -> str:
        """
        Constructs a full API endpoint URL by appending the provided endpoint to the base URL.

        Args:
            endpoint (str): The specific API endpoint to be appended to the base URL.

        Returns:
            str: The full API endpoint URL.
        """

        # Append the provided endpoint to the base URL
        return self.CAMB_URL + endpoint


    def get_languages(self, type: Literal["source", "target"],
                      write_to_file: bool = False) -> list[LanguageOptionsDict]:
        """
        Retrieves a list of languages from the API endpoint based on the type specified.

        Args:
            - type (Literal["source", "target"]): Specifies the type of languages to retrieve.
                Can be either "source" for source languages or "target" for target languages.
            - get_languages (bool, optional): If True, retrieves the languages. Defaults to False.

        Returns:
            list[LanguageOptionsDict]: A list of language dictionaries if the request is successful.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """
        # Construct the API endpoint URL
        url: str = self.create_api_endpoint(f"{type}_languages")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        if write_to_file:
            with open(f"{type}_languages.json", "w") as f:
                f.write(response.text)
            print(f"{type} languages written to {type}_languages.json")

        # Return the response data as a list of language dictionaries
        return response.json()


    def get_all_voices(self) -> list[dict]:
        """
        Retrieves a list of all voices available in Camb AI.

        This method sends a GET request to the "list_voices" endpoint of the Camb AI API.
        If the request is successful, it returns a list of dictionaries, each representing a voice.

        Returns:
            list[dict]: A list of dictionaries, each representing a voice.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """
        # Construct the API endpoint URL for listing voices
        url: str = self.create_api_endpoint("list_voices")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a list of voice dictionaries
        return response.json()

    # ---------- Dub Example ---------- #
    def start_dubbing(self, *, video_url: str, source_language: int = 1,
                      target_language: int) -> dict:
        """
        Starts the dubbing process for a given video URL.

        This method sends a POST request to the "end_to_end_dubbing" endpoint of the Camb AI API.
        The request includes the video URL, source language, and target language as JSON data.

        Args:
            video_url (str): The URL of the video to be dubbed.
            source_language (int, optional): The ID of the source language. Defaults to 1 - English (US)
            target_language (int): The ID of the target language.

        Returns:
            dict: The response from the API as a dictionary.

        Raises:
            HTTPError: If the POST request to the API endpoint fails.
        """
        # Construct the API endpoint URL for end-to-end dubbing
        url: str = self.create_api_endpoint("end_to_end_dubbing")

        # Set the Content-Type header to "application/json"
        self.session.headers["Content-Type"] = "application/json"

        # Prepare the data to be sent in the POST request
        data: dict = {
            "video_url": video_url,
            "source_language": source_language,
            "target_language": target_language
        }

        # Send a POST request to the API endpoint with the prepared data
        response = self.session.post(
            url=url,
            json=data
        )

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a dictionary
        return response.json()


    def get_dubbing_task_status(self, task_id: str) -> DubbingTaskStatus:
        """
        Retrieves the status of a specific dubbing task.

        This method sends a GET request to the "end_to_end_dubbing/{task_id}" endpoint of the Camb
        AI API. The task_id is used to identify the specific dubbing task.

        Args:
            task_id (str): The ID of the dubbing task.

        Returns:
            DubbingTaskStatus: The status of the dubbing task as a dictionary.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """

        # Construct the API endpoint URL for retrieving the status of a specific dubbing task
        url: str = self.create_api_endpoint(f"end_to_end_dubbing/{task_id}")

        # Send a GET request to the API endpoint
        response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a dictionary
        return response.json()


    def get_dubbed_run_info(self, run_id: int) -> DubbedRunInfo:
        """
        Retrieves the dubbed run information for a specific run ID.

        This method sends a GET request to the "dubbed_run_info/{run_id}" endpoint of the Camb AI
        API. The run_id is used to identify the specific run.

        Args:
            run_id (int): The ID of the run.

        Returns:
            DubbedRunInfo: The dubbed run information as a dictionary.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """
        # Construct the API endpoint URL for retrieving the dubbed run information
        url: str = self.create_api_endpoint(f"dubbed_run_info/{run_id}")

        # Send a GET request to the API endpoint
        response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a DubbedRunInfo dictionary
        return response.json()


    def dub(self, *, video_url: str, source_language: int = 1, target_language: int,
                polling_interval:int = 2, debug: bool = False):
        """
        Starts the dubbing process for a given video and periodically checks the status until it's
        done.

        This method first sends a request to start the dubbing process. Then, it enters a loop where
        it periodically checks the status of the dubbing task. If the status is "SUCCESS", it breaks
        the loop.
        If the status is neither "SUCCESS" nor "PENDING", it raises an APIError. If the run ID is
        None after the task is successful, it raises an APIError.

        Args:
            video_url (str): The URL of the video to be dubbed.
            source_language (int, optional): The ID of the source language. Defaults to 1 - English (US)
            target_language (int): The ID of the target language.
            polling_interval (int, optional): The interval in seconds between each status check.
            Defaults to 2 seconds.
            debug (bool, optional): If True, prints the task status and run ID at each status check. Defaults to False.

        Returns:
            DubbedRunInfo: The dubbed run information as a dictionary.

        Raises:
            APIError: If the task status is neither "SUCCESS" nor "PENDING", or if the run ID is
            None.
        """
        # Initialize variables for the dubbing task status and task ID
        task: DubbingTaskStatus
        task_id: str

        print("Starting Dubbing")

        # Start the dubbing process
        response = self.start_dubbing(video_url=video_url, source_language=source_language,
                                      target_language=target_language)

        print(f"Dubbing Task Started: {response}")

        # Extract the task ID from the response
        task_id = response["task_id"]

        # Enter a loop to periodically check the status of the dubbing task
        while True:
            # Get the current status of the dubbing task
            task = self.get_dubbing_task_status(task_id)

            # If debug is True, print the task status and run ID
            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")

            # If the task status is "SUCCESS", break the loop
            if task["status"] == "SUCCESS":
                break

            # If the task status is neither "SUCCESS" nor "PENDING", raise an APIError
            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(f"Dubbing Issue: {task['status']} for Run ID: {task['run_id']}")

            # Wait for the specified polling interval before the next status check
            sleep(polling_interval)

        # Get the final status of the dubbing task
        task = self.get_dubbing_task_status(task_id)

        # If the run ID is None, raise an APIError
        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Return the dubbed run information
        return self.get_dubbed_run_info(task["run_id"])
