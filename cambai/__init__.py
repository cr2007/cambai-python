import os
import sys
import math
import json
from time import sleep
from typing import Optional, Literal, TypedDict
from enum import IntEnum
import requests
from rich import print
from tqdm import tqdm

# For Python < 3.9, use 'List' and 'Dict' from 'typing'
if sys.version_info < (3, 9):
    from typing import List as list, Dict as dict


# ---------- Error Classes ---------- #

class APIKeyMissingError(Exception):
    """Exception raised when the API Key is missing."""


class APIError(Exception):
    """Exception raised when an API error occurs. \n
    Mostly when a non-200 status code is returned."""

# ---------- TypedDict for Error Handling ---------- #

class ErrorDetail(TypedDict):
    """
    Represents the structure of an error detail in a response.

    Attributes:
        loc (list[str]): A list of location strings indicating where the error occurred.
        msg (str): The error message.
        type (str): The type of error.
    """
    loc: list[str]
    msg: str
    type: str


class ErrorResponse(TypedDict):
    """
    Represents the structure of an error response.

    Attributes:
        detail (list[ErrorDetail]): A list of error details, each providing specific information
        about an individual error encountered.
    """
    detail: list[ErrorDetail]

# ---------- Language and Gender Options ---------- #

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


class Gender(IntEnum):
    """
    This Enum class represents the gender categories.

    Attributes:
    - NOT_KNOWN (int): Gender is not known.
    - MALE (int): Male gender.
    - FEMALE (int): Female gender.
    - NOT_APPLICABLE (int): Gender is not applicable.
    """
    NOT_KNOWN = 0
    MALE = 1
    FEMALE = 2
    NOT_APPLICABLE = 9

# ---------- Voices List ---------- #

class VoicesListDict(TypedDict):
    """
    This class represents a dictionary that maps voice properties to their values.
    It is a TypedDict which enforces a specific set of keys with values of specific types.

    Attributes:
        id (int): The unique identifier for a voice.
        voice_name (str): The name of the voice.
    """
    id: int
    voice_name: str


class VoiceProperties(TypedDict):
    """
    Represents the properties of a voice.

    Attributes:
        voice_name (str): The name of the voice.
        gender (int): The gender of the voice, represented as an integer.
        age (int): The age of the voice.
    """
    voice_name: str
    gender: int
    age: int

# ---------- Task Status ---------- #

class TaskStatus(TypedDict):
    """
    A TypedDict representing the status of a dubbing task.

    Attributes:
        - status (Literal["SUCCESS", "PENDING", "TIMEOUT", "ERROR", "PAYMENT_REQUIRED"]):
            The status of the dubbing task. It can be one of the following:
            - "SUCCESS": The task completed successfully.
            - "PENDING": The task is still in progress.
            - "TIMEOUT": The task timed out before completion.
            - "ERROR": An error occurred during the task.
            - "PAYMENT_REQUIRED": Payment is required to complete the task.
        - run_id (Optional[int]): The unique identifier for the task run. It can be None if the task
          has not started yet.
    """
    status: Literal["SUCCESS", "PENDING", "TIMEOUT", "ERROR", "PAYMENT_REQUIRED"]
    run_id: Optional[int]

# ---------- Transcription Result ---------- #

class TranscriptionResult(TypedDict):
    """
    Represents a single transcription result.

    This class is a TypedDict used for type hinting purposes, defining the structure of a
    transcription result. It includes the start and end times of the spoken segment, the transcribed
    text, and the identified speaker.

    Attributes:
        - start (float): The start time of the transcribed segment, in seconds.
        - end (float): The end time of the transcribed segment, in seconds.
        - text (str): The transcribed text of the segment.
        - speaker (str): The identifier for the speaker in the segment.
    """
    start: float
    end: float
    text: str
    speaker: str

# ---------- Dubbing Information ---------- #

class DubbedRunInfo(TypedDict):
    """
    Represents information about a dubbed run, including URLs for the video and audio,
    and the transcription results.

    Attributes:
        - video_url (`str`): The URL of the video associated with the dubbed run.
        - audio_url (`str`): The URL of the audio track used in the dubbed video.
        - transcript (`list[TranscriptionResult]`): A list of transcription results,
                                                each representing a segment of the audio
                                                transcribed to text.
    """
    video_url: str
    audio_url: str
    transcript: list[TranscriptionResult]

# ---------- Translation Information ---------- #

class BasicTranslationData(TypedDict, total=True):
    """
    Represents the basic data required for a translation request.

    Attributes:
        - source_language (int): The ID of the source language.
        - target_language (int): The ID of the target language.
        - text (str): The text to be translated.
    """

    source_language: int
    target_language: int
    text:            str

class ExtendedTranslationData(BasicTranslationData, total=False):
    """
    Extends BasicTranslationData with optional parameters for a more customized translation request.

    Attributes:
        - age (Optional[int]): The age of the text's intended audience. Used to tailor the
                               translation.
        - formality (Optional[int]): The formality level of the translation. Can be informal or
                                     formal.
        - gender (Optional[int]): The gender of the text's intended audience. Used to adjust the
                                  translation accordingly.
    """

    age:       Optional[int]
    formality: Optional[int]
    gender:    Optional[int]

# ------------------------------------------------------------------------------------------------ #

class CambAI:
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
        self.camb_api_url: str = "https://client.camb.ai/apis/"

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
        return self.camb_api_url + endpoint


    def get_languages(self, language_type: Literal["source", "target"],
                      write_to_file: bool = False) -> list[LanguageOptionsDict]:
        """
        Retrieves a list of languages from the API endpoint based on the type specified.

        Args:
            - language_type (Literal["source", "target"]): Specifies the type of languages to
                retrieve.
                Can be either "source" for source languages or "target" for target languages.
            - get_languages (bool, optional): If True, retrieves the languages. Defaults to False.

        Returns:
            list[LanguageOptionsDict]: A list of language dictionaries if the request is successful.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """
        # Construct the API endpoint URL
        url: str = self.create_api_endpoint(f"{language_type}_languages")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        if write_to_file:
            with open(f"{language_type}_languages.json", "w", encoding="utf-8") as file:
                json.dump(response.json(), file, indent=4)
            print(f"{language_type} languages written to {language_type}_languages.json")

        # Return the response data as a list of language dictionaries
        return response.json()

    # ---------- Voices ---------- #

    def create_custom_voice(self, *, voice_name: str, gender: Gender, age: int = 30,
                            file: str) -> Optional[dict[str, str]]:
        """
        Creates a custom voice profile based on the provided parameters.

        This method sends a request to a predefined API endpoint to create a custom voice profile.
        It requires a voice name, Gender (as an instance of a Gender Enum), and optionally an age
        and a file path to an audio sample.

        Parameters:
        - voice_name (str): The name to assign to the custom voice.
        - gender (Gender): The gender of the voice. Must be an instance of the Gender Enum.
        - age (int, optional): The age of the voice. Defaults to 30.
        - file (str): The file path to an audio sample for the custom voice.

        Returns:
        - dict[str, int]: A dictionary containing the response from the API.

        Raises:
        - TypeError: If the gender is not an instance of the Gender Enum.
        - requests.HTTPError: If the response status code from the API is not 200.

        Note:
        - The 'file' parameter should be a valid path to an audio file.
        - Ensure the 'Gender' Enum is imported before calling this method.
        """

        # Check if the gender is an instance of the Gender Enum
        if not isinstance(gender, Gender):
            raise TypeError("Gender must be an instance of Gender Enum.\n",
                            "Make sure you have imported the 'Gender' Enum")

        if not file.endswith(".wav"):
            raise ValueError(f"File '{file}' is not a WAV file.")

        # Construct the API endpoint URL
        url: str = self.create_api_endpoint("create_custom_voice")

        # Prepare the data payload with voice properties
        data: VoiceProperties = {
            "voice_name": voice_name,
            "gender": gender.value,
            "age": age
        }

        # Prepare the file to be uploaded using 'with' statement for better resource management
        try:
            with open(file, 'rb') as file_resource:
                # Send a POST request to the API with the file and data
                response: requests.Response = self.session.post(
                    url=url,
                    files={'file': file_resource},
                    data=data
                )

                # If the status code is not 200, raise an HTTPError
                response.raise_for_status()

                # Return the JSON response from the API
                return response.json()
        except FileNotFoundError:
            print("File not found."
                  "Please enter a valid file path containing an audio file to send to the API.")
            return None
        except requests.exceptions.RequestException as e:
            print("There was an exception that occurred while handling your request.", e)
            return None


    def get_all_voices(
        self,
        write_to_file: bool = False
        ) -> list[Optional[VoicesListDict]]:
        """
        This method sends a GET request to the API endpoint to retrieve all voices.
        If write_to_file is True, it writes the response to a JSON file.

        Args:
            write_to_file (bool): If True, writes the response to a JSON file. Defaults to False.

        Returns:
            list[Optional[VoicesListDict]]: A list of dictionaries representing voices.

        Raises:
            HTTPError: If the GET request to the API endpoint fails.
        """

        # Construct the API endpoint URL for listing voices
        url: str = self.create_api_endpoint("list_voices")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # If write_to_file is True, write the response to a JSON file
        if write_to_file:
            # If the file already exists, remove it before writing the new data
            if os.path.exists("voices.json"):
                print("'voices.json' already exists.\n"
                      "Removing the existing file...")
                os.remove("voices.json")

            # Open the file in write mode
            with open("voices.json", "w", encoding="utf-8") as file:
                # Dump the JSON response into the file with indentation for readability
                json.dump(response.json(), file, indent=4)
            print("Voices written to voices.json")

        # Return the response data as a list of voice dictionaries
        return response.json()

    # ---------- Dubbing ---------- #

    def start_dubbing(self, *, video_url: str, source_language: int = 1,
                      target_language: int) -> dict[str, str]:
        """
        Starts the dubbing process for a given video URL.

        This method sends a POST request to the "end_to_end_dubbing" endpoint of the Camb AI API.
        The request includes the video URL, source language, and target language as JSON data.

        Args:
            - video_url (str): The URL of the video to be dubbed.
            - source_language (int, optional): The ID of the source language.
                                                Defaults to 1 - English (US)
            - target_language (int): The ID of the target language.

        Returns:
            - dict: The response from the API as a dictionary.

        Raises:
            - HTTPError: If the POST request to the API endpoint fails.
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
        response: requests.Response = self.session.post(url=url, json=data)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a dictionary
        return response.json()


    def get_task_status(
        self,
        task: Literal["tts", "dubbing", "transcription"],
        task_id: str
        ) -> TaskStatus:
        """
        Retrieves the status of a specific task.

        This method sends a GET request to the appropriate endpoint of the Camb
        AI API based on the task type. The task_id is used to identify the specific task.

        Args:
            - task (str): The type of the task. Must be one of 'dubbing', 'tts', or 'transcription'.
            - task_id (str): The ID of the task.

        Returns:
            - TaskStatus: The status of the task as a dictionary.

        Raises:
            - ValueError: If the task type is not valid.
            - HTTPError: If the GET request to the API endpoint fails.
        """

        # Initialize 'url' with an empty string
        url: str = ""

        # Determine the appropriate API endpoint based on the task type
        if task == "dubbing":
            url: str = self.create_api_endpoint(f"end_to_end_dubbing/{task_id}")
        elif task == "tts":
            url: str = self.create_api_endpoint(f"tts/{task_id}")
        elif task == "transcription":
            url: str = self.create_api_endpoint(f"create_transcription/{task_id}")
        else:
            raise ValueError("Invalid task type. Must be one of 'dubbing', 'tts',"
                             "or 'transcription'")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

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
        response: requests.Response = self.session.get(url)

        # If the status code is not 200, raise an HTTPError
        response.raise_for_status()

        # Return the response data as a DubbedRunInfo dictionary
        return response.json()


    def dub(self, *, video_url: str, source_language: int = 1, target_language: int,
                polling_interval: float = 2, debug: bool = False) -> DubbedRunInfo:
        """
        Starts the dubbing process for a given video and periodically checks the status until it's
        done.

        This method first sends a request to start the dubbing process. Then, it enters a loop where
        it periodically checks the status of the dubbing task. If the status is "SUCCESS", it breaks
        the loop.\n
        If the status is neither "SUCCESS" nor "PENDING", it raises an APIError. If the run ID is
        None after the task is successful, it raises an APIError.

        Args:
            - video_url (str): The URL of the video to be dubbed.
            - source_language (int, optional): The ID of the source language.
                                                Defaults to 1 - English (US)
            - target_language (int): The ID of the target language.
            - polling_interval (int, optional): The interval in seconds between each status check.
            Defaults to 2 seconds.
            - debug (bool, optional): If True, prints the task status and run ID at each status
                                        check. Defaults to False.

        Returns:
            DubbedRunInfo: The dubbed run information as a dictionary.

        Raises:
            APIError: If the task status is neither "SUCCESS" nor "PENDING", or if the run ID is
            None.
        """

        # Initialize variables for the dubbing task status and task ID
        task: TaskStatus
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
            task = self.get_task_status("dubbing", task_id)

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
            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            for _ in tqdm(range(math.ceil(polling_interval)), unit="s",
                          desc=f"Waiting {polling_interval} seconds before checking status again"):
                sleep(1)

        # Get the final status of the dubbing task
        task = self.get_task_status("dubbing", task_id)

        # If the run ID is None, raise an APIError
        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Return the dubbed run information
        return self.get_dubbed_run_info(task["run_id"])

    # ---------- TTS ---------- #

    def create_tts(self, /, text: str, voice_id: int, language: int, *, gender: Gender,
                   age: Optional[int] = None) -> dict[str, str]:
        """
        Create a text-to-speech (TTS) request.

        Args:
            text (str): The text to be converted to speech.
            voice_id (int): The ID of the voice to be used.
            language (int): The ID of the language to be used.
            gender (Gender): The gender of the voice. Must be an instance of the Gender Enum.
            age (Optional[int]): The age of the voice. If not provided, a default value will be used

        Raises:
            TypeError: If the gender is not an instance of the Gender Enum.
            ValueError: If the language ID is not between 1 and 148.

        Returns:
            dict: The JSON response from the TTS API.
        """

        # Check if the gender is an instance of the Gender Enum
        if not isinstance(gender, Gender):
            raise TypeError("Gender must be an instance of Gender Enum.\n",
                            "Make sure you have imported the 'Gender' Enum")

        # Check if the language ID is not within the valid range
        if not 1 <= language <= 148:
            raise ValueError("Language ID must be between 1 and 148")

        # Create the API endpoint URL
        url: str = self.create_api_endpoint("tts")

        # Prepare the data to be sent in the request
        data: dict = {
            "text": text,
            "voice_id": voice_id,
            "language": language,
            "gender": gender.value,
            "age": age
        }

        # Set the Content-Type header to 'application/json'
        self.session.headers["Content-Type"] = "application/json"

        # Send the POST request to the API
        response: requests.Response = self.session.post(url=url, json=data)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Return the JSON response from the API
        return response.json()


    def get_tts_status(self, task_id: str) -> TaskStatus:
        """
        Get the status of a text-to-speech (TTS) task.

        Args:
            task_id (str): The ID of the TTS task.

        Raises:
            HTTPError: If the GET request to the TTS API fails.

        Returns:
            TaskStatus: The status of the TTS task.
        """

        return self.get_task_status("tts", task_id)


    def get_tts_result(self, run_id: int, output_directory: Optional[str]) -> None:
        """
        This method retrieves the Text-to-Speech (TTS) result from a specific API endpoint and saves
        it as a .wav file.

        Parameters:
        - `run_id` (int): The ID of the run for which the TTS result is to be fetched.
        - `output_directory` (Optional[str]): The directory where the .wav file will be saved. If
        `None`, defaults to "audio_tts".

        Returns:
        None
        """

        # Check if output_directory is None and set it to default if it is
        if output_directory is None:
            output_directory = "audio_tts"

        # Create the API endpoint URL using the provided run_id
        url: str = self.create_api_endpoint(f"tts_result/{run_id}")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url, stream=True)

        # Raise an HTTPError if one occurred
        response.raise_for_status()

        # Check if the output directory exists
        if not os.path.exists(output_directory):
            print("File directory does not exist. Creating directory...")
            # Create the directory if it doesn't exist
            os.makedirs(output_directory)

        # Open a .wav file in the output directory to write the TTS result
        file_path: str = f"{output_directory}/tts_stream_{run_id}.wav"
        with open(file_path, "wb") as audio_file:
            # Write the response content to the .wav file in chunks of 1024 bytes
            for chunk in response.iter_content(chunk_size=1024):
                audio_file.write(chunk)

            # Print success message
            print(f"\nTTS audio written to '{file_path}'")


    def tts(self, *, text: str, voice_id: int, language: int, gender: Gender,
            age: Optional[int] = None, polling_interval: float = 2, debug: bool = False,
            output_directory: str = "audio_tts") -> None:
        """
        This method initiates a Text-to-Speech (TTS) process, monitors its status, and retrieves the
        result when ready.

        Parameters:
        - text (str): The text to be converted to speech.
        - voice_id: The ID of the voice to be used for the TTS.
        - language (int): The language code for the TTS.
        - gender (Gender): The gender of the voice for the TTS.
        - age (Optional[int]): The age of the voice for the TTS. If None, no specific age is set.
        - polling_interval (float): The interval (in seconds) at which the TTS status is checked.
          Defaults to 2.
        - debug (bool): If True, debug information is printed. Defaults to False.
        - output_directory (str): The directory where the .wav file will be saved. If None, defaults
          to "audio_tts".

        Returns:
        None
        """

        # Initialize task status and task ID
        task: TaskStatus
        task_id: str

        # Print debug information if debug is True
        if debug:
            print("Starting TTS process\n")

        # Create the TTS task
        response = self.create_tts(text=text, voice_id=voice_id, language=language,
                                    gender=gender, age=age)

        # Print the response containing the task ID from the TTS task creation
        print(f"TTS Task Started: {response}\n")

        # Extract the task ID from the response
        task_id = response["task_id"]

        # Continuously check the status of the TTS task
        while True:
            # Get the current status of the TTS task
            task = self.get_tts_status(task_id)

            # Print debug information if debug is True
            if debug:
                print(f"TTS Status: {task['status']}, Run ID: {task['run_id']}")

            # Break the loop if the task status is "SUCCESS"
            if task["status"] == "SUCCESS":
                break

            # Raise an error if the task status is neither "SUCCESS" nor "PENDING"
            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(f"Issue with TTS: {task['status']} for Run ID: {task['run_id']}")

            # Wait for the specified polling interval before the next status check
            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            for _ in tqdm(range(math.ceil(polling_interval)), unit="s",
                          desc=f"Waiting {polling_interval} seconds before checking status again"):
                sleep(1)

        # Get the status of the TTS task
        task = self.get_task_status(task="tts", task_id=task_id)

        # Raise an error if the run ID is None
        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Get the TTS result and save it to the specified output directory
        self.get_tts_result(run_id=task["run_id"], output_directory=output_directory)

    # ---------- Transcription ---------- #

    def create_transcription(self, /, audio_file: str, language: int) -> dict[str, str]:
        """
        Creates a transcription request for an audio file with the specified language.

        This method sends an audio file to a predefined API endpoint for transcription. The API
        expects the language to be specified as an integer ID within a valid range. The method
        checks if the provided language ID is within the valid range before sending the request.

        Parameters:
            - `audio_file` (str): The file path of the audio file to be transcribed.
            - `language` (int): The language ID for the transcription, must be within 1 to 148.

        Returns:
            - `dict[str, str]`: The JSON response from the API if successful. If an error occurs, a
            dictionary with an appropriate error message is returned.

        Raises:
            - `ValueError`: If the language ID is not within the valid range.
            - `FileNotFoundError`: If the specified audio file does not exist.
        """
        # Check if the language ID is not within the valid range
        if not 1 <= language <= 148:
            raise ValueError("Language ID must be between 1 and 148")

        # Construct the API endpoint URL
        url: str = self.create_api_endpoint("create_transcription")

        # Prepare the data payload with the language ID
        data: dict[str, int] = {
            "language": language
        }

        try:
            # Open the audio file in binary read mode
            with open(audio_file, "rb") as audio:
                # Make a POST request to the API with the audio file and language ID
                response: requests.Response = self.session.post(
                    url=url,
                    files={"file": audio},  # The audio file to be transcribed
                    data=data  # Additional data including the language ID
                )

                # Check if the response status code indicates a successful request
                if response.status_code != 200:
                    print("Error: There was an error with your POST request.")

                # Return the JSON response from the API
                return response.json()
        except FileNotFoundError:
            # Handle the case where the specified audio file does not exist
            print("File not found."
                    "Please enter a valid file path containing an audio file to send to the API.")
            return {"FileNotFoundError": "Enter a valid file path to the audio file"}


    def get_transcription_result(self, *, run_id: int,
                                 save_to_file: bool = False) -> list[TranscriptionResult]:
        """
        Retrieves the transcription result for a given run ID and optionally saves it to a file.

        This method contacts a predefined API endpoint to fetch the transcription result associated
        with a specific run ID. If the `save_to_file` flag is set to True, the method will also save
        the transcription result to a JSON file on disk.

        Parameters:
            - `run_id` (int): The unique identifier for the transcription run.
            - `save_to_file` (bool): A flag indicating whether to save the transcription result to a
                                 file. Defaults to False.

        Returns:
            - list[TranscriptionResult]: A list of transcription results. Each result is represented
                                       as a `TranscriptionResult` object.

        Raises:
            - HTTPError: If the request to the API endpoint does not return a 200 status code.
        """

        # Construct the API endpoint URL using the provided run ID
        url: str = self.create_api_endpoint(f"transcription_result/{run_id}")

        # Perform a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # Check if the response status code indicates a successful request
        if response.status_code != 200:
            # Raise an HTTPError if the request was not successful
            raise requests.HTTPError("Error: There was an error with your request."
                                     f"Status code: {response.status_code}")

        # If the save_to_file flag is True, save the transcription result to a JSON file
        if save_to_file:
            with open(f"transcription_result_{run_id}.json", "w", encoding="utf-8") as output_file:
                # Serialize JSON response with pretty printing and write it to the specified file
                json.dump(response.json(), output_file, indent=4)

        # Return the JSON response as a list of TranscriptionResult objects
        return response.json()


    def transcribe(self, *, audio_file: str, language: int, save_to_file: bool = False,
                   polling_interval: float = 2, debug: bool = False) -> list[TranscriptionResult]:
        """
        Transcribes the given audio file to text in the specified language, optionally saving the
        result to a file.

        This method initiates a transcription task for an audio file, periodically checks for the
        task's completion,
        and retrieves the transcription result. It supports optional debugging output and can save
        the transcription results to a file if requested.

        Parameters:
            - audio_file (str): The path to the audio file to be transcribed.
            - language (int): The language code for the transcription service to use.
            - save_to_file (bool): If True, saves the transcription result to a file. Defaults to
                                   False.
            - polling_interval (float): The time interval, in seconds, between status checks of the
                                       transcription task.
                                       Defaults to 2 seconds.
            - debug (bool): If True, prints debugging information during the transcription process.
                          Defaults to False.

        Returns:
            - list[TranscriptionResult]: A list of transcription results, each represented as a
              `TranscriptionResult` object.

        Raises:
            APIError: If the transcription task fails or if the run ID is None after the task
                      completes.
        """

        task: TaskStatus
        task_id: str

        print("Starting Transcription")

        # Create a new transcription task with the specified audio file and language
        response = self.create_transcription(audio_file, language)

        print(f"Transcription Task Started: {response}")

        task_id = response["task_id"]

        while True:
            # Check the current status of the transcription task
            task = self.get_task_status("transcription", task_id)

            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")

            if task["status"] == "SUCCESS":
                # Exit the loop if the task is successfully completed
                break

            if task["status"] not in ["SUCCESS", "PENDING"]:
                # Raise an error if the task status indicates a failure
                raise APIError(f"Dubbing Issue: {task['status']} for Run ID: {task['run_id']}")

            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            # Wait for the specified polling interval with a progress bar
            for _ in tqdm(range(math.ceil(polling_interval)), unit="s",
                          desc=f"Waiting {polling_interval} seconds before checking status again"):
                sleep(1)

        # Retrieve the final task status to get the run ID
        task = self.get_task_status("transcription", task_id)

        if task["run_id"] is None:
            # Raise an error if the run ID is missing
            raise APIError("Run ID is None")

        # Retrieve and return the transcription result
        return self.get_transcription_result(
            run_id=task["run_id"],
            save_to_file=save_to_file
        )

    # ---------- Translation ---------- #

    def create_translation(
            self,
            *,
            source_language: int,
            target_language: int,
            text: str,
            age: int,
            formality: Optional[int] = None,
            gender: Optional[Gender] = None
            ) -> dict[str, str]:
        """
        Creates a translation request and sends it to the translation API.

        This method constructs a translation request with mandatory and optional parameters,
        validates the parameters, and sends the request to the specified translation API endpoint.
        It returns the response in JSON format.

        Parameters:
            - source_language (int): The ID of the source language.
            - target_language (int): The ID of the target language.
            - text (str): The text to be translated.
            - age (int): The age of the text's intended audience.
            - formality (Optional[int]): The formality level of the translation, if applicable.
            - gender (Optional[Gender]): The gender of the text's intended audience, if applicable.

        Returns:
            - dict[str, str]: The response from the translation API in JSON format.

        Raises:
            - ValueError: If any of the language IDs or formality values are out of their valid
                          range.

        Note:
            - The `source_language` and `target_language` IDs must be within the range [1, 148].
            - The `formality` parameter, if provided, must be either 1 or 2.
            - The `gender` parameter, if provided, must be an instance of the `Gender` enum.
        """

        # Validate source language ID
        if not 1 <= source_language <= 148:
            raise ValueError("create_translation: Source Language must be an integer"
                             "value between 1 and 148. To know more, call"
                             "the 'get_languages(\"source\")' function")

        # Validate target language ID
        if not 1 <= target_language <= 148:
            raise ValueError("create_translation: Target Language must be an integer value"
                             "between 1 and 148. To know more, call the"
                             "'get_languages(\"target\")' function")

        # Validate formality, if provided
        if (formality is not None) and (formality not in {1, 2}):
            raise ValueError("create_translation: formality must be one of {1, 2}")

        # Check if the gender is an instance of the Gender Enum
        if (gender is not None) and (not isinstance(gender, Gender)):
            raise TypeError("Gender must be an instance of Gender Enum.\n",
                            "Make sure you have imported the 'Gender' Enum")

        # Construct the API endpoint URL
        url: str = self.create_api_endpoint("create_translation")

        # Set the content type for the request
        self.session.headers["Content-Type"] = "application/json"

        # Construct the data payload for the POST request
        data: ExtendedTranslationData = {
            "source_language": source_language,
            "target_language": target_language,
            "text": text
        }

        # Add optional parameters to the payload, if provided
        if age is not None:
            data["age"] = age
        if formality is not None:
            data["formality"] = formality
        if gender is not None:
            data["gender"] = gender.value

        # Send the POST request to the API
        response: requests.Response = self.session.post(
            url=url,
            json=data
        )

        # Check for successful response
        if response.status_code != 200:
            print("Error: There was an error with your POST request.")

        # Return the JSON response
        return response.json()
