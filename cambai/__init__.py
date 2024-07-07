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


# ---------- Language and Gender Options ---------- #


class LanguageOptionsDict(TypedDict):
    """
    Represents a dictionary containing language options.

    Attributes:
        id (int): The ID of the language option.
        language (str): The name of the language.
        short_name (str): The short name of the language.
    """

    id:         int
    language:   str
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

    id:         int
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
    gender:     int
    age:        Optional[int]


# ---------- Task Status ---------- #


class TaskInfo(TypedDict):
    """
    Represents the object returned from a task creation.

    Attributes:
        - task_id (str): A unique identifier for the task.
    """

    task_id: str


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
        - run_id (int, Optional): The unique identifier for the task run. It can be None if the task
          has not started yet.
    """

    status: Literal["SUCCESS", "PENDING", "TIMEOUT", "ERROR", "PAYMENT_REQUIRED"]
    run_id: Optional[int]


# ---------- Transcription Result ---------- #


class TranscriptionResult(TypedDict):
    """
    Represents a single transcription result.

    This class is a TypedDict used for type hinting purposes, defining the structure of a
    transcription result.\\
    It includes the start and end times of the spoken segment, the transcribed text, and the
    identified speaker.

    Attributes:
        - start (float): The start time of the transcribed segment, in seconds.
        - end (float): The end time of the transcribed segment, in seconds.
        - text (str): The transcribed text of the segment.
        - speaker (str): The identifier for the speaker in the segment.
    """

    start:   float
    end:     float
    text:    str
    speaker: str


# ---------- Dubbing Information ---------- #


class DubbedRunInfo(TypedDict):
    """
    Represents information about a dubbed run, including URLs for the video and audio, and the
    transcription results.

    Attributes:
        - `video_url` (str): The URL of the video associated with the dubbed run.
        - `audio_url` (str): The URL of the audio track used in the dubbed video.
        - `transcript` (list[TranscriptionResult]): A list of transcription results, each
            representing a segment of the audio transcribed to text.
    """

    video_url:  str
    audio_url:  str
    transcript: list[TranscriptionResult]


# ---------- Translation Information ---------- #


class BasicTranslationData(TypedDict, total=True):
    """
    Represents the basic data required for a translation request.

    Attributes:
        - `source_language` (int): The ID of the source language.
        - `target_language` (int): The ID of the target language.
        - `text` (str): The text to be translated.
    """

    source_language: int
    target_language: int
    text:            str


class ExtendedTranslationData(BasicTranslationData, total=False):
    """
    Extends BasicTranslationData with optional parameters for a more customized translation request.

    Attributes:
        - `age` (int, Optional): The age of the text's intended audience. Used to tailor the
                               translation.
        - `formality` (int, Optional): The formality level of the translation. Can be informal or
                                     formal.
        - `gender` (int, Optional): The gender of the text's intended audience. Used to adjust the
                                  translation accordingly.
    """

    age:       Optional[int]
    formality: Optional[int]
    gender:    Optional[int]


class TranslationResult(TypedDict):
    """
    Represents the result of a translation operation.

    Attributes:
        - `text` (str): The translated text.
    """

    text: str


# ---------- Translation TTS Information ---------- #


class BasicTranslationTTSData(BasicTranslationData, total=True):
    """
    Represents the data model for basic translation with Text-to-Speech (TTS) information.

    This class extends `BasicTranslationData` by including TTS-specific information, such as the
    voice ID used for the TTS output.\\
    It is designed to be used in scenarios where translation output needs to be synthesized into
    speech, requiring a specific voice.

    Attributes:
        - `voice_id` (int): An identifier for the voice to be used in TTS synthesis. This ID
        corresponds to a specific voice in the TTS system.
    """

    voice_id: int


class ExtendedTranslationTTSData(BasicTranslationTTSData, total=False):
    """
    Extends BasicTranslationTTSData with optional attributes for more detailed TTS customization.

    This class builds upon `BasicTranslationTTSData` by introducing additional optional attributes
    that allow for more granular control over the Text-to-Speech (TTS) output.\\
    These attributes include age, formality, and gender, enabling users to tailor the TTS voice to
    better suit the context or audience of the translation.

    Attributes:
        - `age` (int, Optional): Specifies the desired age group of the TTS voice. This can
            influence the perceived age of the voice in the TTS output.
        - `formality` (int, Optional): Indicates the desired level of formality for the TTS voice.
            This can affect the speaking style, potentially making it more formal or casual
            depending on the value.
        - `gender` (int, Optional): Specifies the desired gender of the TTS voice. This allows for
            the selection of a voice that aligns with a specific gender identity.
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


    def __create_api_endpoint(self, /, endpoint: str) -> str:
        """
        Constructs a full API endpoint URL by appending the provided endpoint to the base URL.

        Args:
            `endpoint` (str): The specific API endpoint to be appended to the base URL.

        Returns:
            str: The full API endpoint URL.
        """

        # Append the provided endpoint to the base URL
        return self.camb_api_url + endpoint


    def get_languages(
        self, /, language_type: Literal["source", "target"], write_to_file: bool = False
    ) -> list[LanguageOptionsDict]:
        """
        Fetches the available languages from the API based on the language type.

        This method sends a GET request to the API endpoint to retrieve either source or target
        languages supported by the service. The languages can optionally be written to a JSON file.

        Args:
            - `language_type` (Literal["source", "target"]): Specifies the type of languages to
                fetch. Can be either 'source' for source languages or 'target' for target languages.
            - `write_to_file` (bool, optional): If True, the fetched languages will be written to a
                JSON file. Defaults to False.

        Returns:
            - list[LanguageOptionsDict]: A list of dictionaries, where each dictionary contains
            details about a language supported by the service.

        Raises:
            - SystemExit: If the API request is unsuccessful (i.e., does not return a 200 status
                code), the function prints an error message along with the response details and
                exits.
        """

        # Construct the API endpoint URL based on the language type
        url: str = self.__create_api_endpoint(f"{language_type}_languages")

        # Send a GET request to the constructed URL
        response: requests.Response = self.session.get(url)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # If write_to_file is True, write the response data to a JSON file
        if write_to_file:
            with open(f"{language_type}_languages.json", "w", encoding="utf-8") as file:
                json.dump(response.json(), file, indent=4)
            print(
                f"{language_type} languages written to {language_type}_languages.json"
            )

        # Return the list of language details as a response
        return response.json()

    # ---------- Voices ---------- #

    def create_custom_voice(
        self, *, voice_name: str, gender: Gender, age: Optional[int] = 30, file: str
    ) -> dict[str, str]:
        """
        Creates a custom voice profile using the provided voice sample.

        This method sends a POST request to the API with the voice sample and properties to create a
        custom voice profile.
        The voice properties include the name, gender, and optionally the age of the voice to be
        created.

        Args:
            - `voice_name` (str): The name to assign to the custom voice.
            - `gender` (Gender): The gender of the voice. Must be an instance of the Gender Enum.
            - `age` (Optional[int], optional): The age of the voice. Defaults to 30 if not provided.
            - `file` (str): The file path to the WAV file containing the voice sample.

        Returns:
            - dict[str, str]: A dictionary containing the response from the API. Typically includes
            details of the created voice profile.

        Raises:
            - TypeError: If the gender is not an instance of the Gender Enum.
            - ValueError: If the provided file is not a WAV file.
            - FileNotFoundError: If the specified file does not exist.
            - requests.exceptions.RequestException: For errors encountered during the API request.

        Note:
            The file must be a WAV file and exist at the specified path for the request to succeed.
        """

        # Validate the gender argument is an instance of Gender Enum
        if not isinstance(gender, Gender):
            raise TypeError(
                "Gender must be an instance of Gender Enum.\n",
                "Make sure you have imported the 'Gender' Enum",
            )

        # Validate the file argument ends with .wav extension
        if not file.endswith(".wav"):
            raise ValueError(f"File '{file}' is not a WAV file.")

        # Construct the API endpoint URL
        url: str = self.__create_api_endpoint("create_custom_voice")

        # Prepare the data payload for the POST request
        data: VoiceProperties = {
            "voice_name": voice_name,
            "gender": gender.value,
            "age": None
        }

        # If age is provided, add it to the data payload
        if age is not None:
            data["age"] = age

        try:
            # Open the file in binary read mode and send the POST request
            with open(file, "rb") as file_resource:
                response: requests.Response = self.session.post(
                    url=url, files={"file": file_resource}, data=data
                )

                # Check for a successful response (status code 200)
                if response.status_code != 200:
                    # Print error details and exit if the request was unsuccessful
                    print(f"Error: There was a {response.status_code} error"
                          "when setting up your custom voice.")
                    print("Response: "
                          f"{response.text if response.status_code == 500 else response.json()}")
                    print("Kindly fix the issue and try again.")
                    sys.exit(1)

                # Return the API response as a dictionary
                return response.json()
        except FileNotFoundError:
            # Handle the case where the specified file does not exist
            print(
                "File not found."
                "Please enter a valid file path containing an audio file to send to the API."
            )
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            # Handle other exceptions related to the requests library
            print(
                "There was an exception that occurred while handling your request.", e
            )
            sys.exit(1)


    def get_all_voices(
        self, *, write_to_file: bool = False
    ) -> list[Optional[VoicesListDict]]:
        """
        Retrieves a list of all available voice options from the API.

        This method sends a GET request to the API to fetch a comprehensive list of voices.
        Optionally, the list can be written to a JSON file for persistence or further processing.

        Args:
            - `write_to_file` (bool, optional): If True, the retrieved list of voices will be saved
                to a file named 'voices.json'.\\
                If 'voices.json' already exists, it will be overwritten. Defaults to False.

        Returns:
            - list[Optional[VoicesListDict]]: A list of dictionaries, each representing a voice
            option. The structure of the dictionaries is defined by the VoicesListDict type hint.

        Raises:
            - SystemExit: If the API request fails (i.e., does not return a 200 status code), an
                error message is printed, and the program exits.

        Note:
            - The method checks for the existence of 'voices.json' before attempting to write to it,
            to avoid unintentional data loss. If the file exists, it is first removed.
        """

        # Construct the API endpoint URL for listing voices
        url: str = self.__create_api_endpoint("list_voices")

        # Send a GET request to the constructed URL
        response: requests.Response = self.session.get(url)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # If write_to_file is True, write the response data to 'voices.json'
        if write_to_file:
            # Check if 'voices.json' already exists and remove it if it does
            if os.path.exists("voices.json"):
                print("'voices.json' already exists.")
                print("Removing the existing file...")
                os.remove("voices.json")

            # Write the JSON response to 'voices.json'
            with open("voices.json", "w", encoding="utf-8") as file:
                json.dump(response.json(), file, indent=4)
            print("Voices written to 'voices.json'")

        # Return the response data as a list of voice dictionaries
        return response.json()

    # ---------- Dubbing ---------- #

    def start_dubbing(
        self, /, video_url: str, source_language: int, target_language: int
    ) -> TaskInfo:
        """
        Initiates the dubbing process for a given video from one language to another.

        This method sends a POST request to the API with the video URL and the source and target
        languages specified by their IDs.
        On success, it returns information about the dubbing task.

        Args:
            - `video_url` (str): The URL of the video to be dubbed.
            - `source_language` (int): The ID of the source language.
            - `target_language` (int): The ID of the target language.

        Returns:
            - TaskInfo: A dictionary containing information about the initiated dubbing task, such
            as task ID and status.

        Raises:
            - SystemExit: If the API request fails (i.e., does not return a 200 status code), prints
            an error message along with the response details and exits the program.
        """

        # Construct the API endpoint URL for initiating dubbing
        url: str = self.__create_api_endpoint("end_to_end_dubbing")

        # Set the content type for the request to JSON
        self.session.headers["Content-Type"] = "application/json"

        # Prepare the data payload for the POST request
        data: dict = {
            "video_url": video_url,
            "source_language": source_language,
            "target_language": target_language,
        }

        # Send a POST request with the video URL and language IDs
        response: requests.Response = self.session.post(url=url, json=data)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your POST request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the response data as a TaskInfo dictionary
        return response.json()


    def get_task_status(
        self,
        /,
        task: Literal["tts", "dubbing", "transcription", "translation", "translated_tts"],
        task_id: str
    ) -> TaskStatus:
        """
        Retrieves the status of a specified task by its ID.

        This method determines the appropriate API endpoint based on the task type and sends a GET
        request to fetch the current status of the task.

        The task can be of types: text-to-speech (tts), dubbing, transcription, or translation.

        Args:
            - `task` (Literal["tts", "dubbing", "transcription", "translation"]): The type of the
                task for which the status is being requested.
            - `task_id` (str): The unique identifier of the task.

        Returns:
            TaskStatus: A dictionary containing the status of the task, including any relevant
                details provided by the API.

        Raises:
            ValueError: If an invalid task type is provided.
            SystemExit: If the API request fails (i.e., does not return a 200 status code), prints
            an error message along with the response details and exits the program.
        """

        # Initialize 'url' with an empty string
        url: str = ""

        # Determine the appropriate API endpoint based on the task type
        if task == "dubbing":
            url: str = self.__create_api_endpoint(f"end_to_end_dubbing/{task_id}")
        elif task == "tts":
            url: str = self.__create_api_endpoint(f"tts/{task_id}")
        elif task == "transcription":
            url: str = self.__create_api_endpoint(f"create_transcription/{task_id}")
        elif task == "translation":
            url: str = self.__create_api_endpoint(f"create_translation/{task_id}")
        elif task == "translated_tts":
            url: str = self.__create_api_endpoint(f"create_translated_tts/{task_id}")
        else:
            raise ValueError(
                "Invalid task type. Must be one of 'dubbing', 'tts', 'transcription', "
                "'translation', or 'translated_tts'."
            )

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the response data as a dictionary
        return response.json()


    def get_dubbed_run_info(self, /, run_id: int) -> DubbedRunInfo:
        """
        Retrieves information about a specific dubbed run by its ID.

        This method sends a GET request to the API using the run ID to fetch detailed information
        about the dubbed run.
        The information includes the status of the dubbing, any errors encountered, and other
        relevant metadata.

        Args:
            - `run_id` (int): The unique identifier of the dubbed run.

        Returns:
            DubbedRunInfo: A dictionary containing detailed information about the dubbed run,
                structured according to the DubbedRunInfo type hint.

        Raises:
            - SystemExit: If the API request fails (i.e., does not return a 200 status code), prints
                an error message along with the response details and exits the program.
        """

        # Construct the API endpoint URL for retrieving the dubbed run information
        url: str = self.__create_api_endpoint(f"dubbed_run_info/{run_id}")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the response data as a DubbedRunInfo dictionary
        return response.json()


    def dub(
        self,
        /,
        video_url: str,
        source_language: int,
        target_language: int,
        *,
        polling_interval: float = 30,
        debug: bool = False,
    ) -> DubbedRunInfo:
        """
        Starts the dubbing process for a given video and periodically checks the status until
        completion.

        This method initiates the dubbing process by sending a request with the video URL and the
        specified source and target languages.

        After initiating the dubbing, it enters a polling loop, checking the dubbing task's status
        at specified intervals. The loop continues until the task status is "SUCCESS".

        If the task status is neither "SUCCESS" nor "PENDING", an exception is raised. Additionally,
        if the run ID is not available after the task reaches a "SUCCESS" status, an exception is
        raised.

        Args:
            - `video_url` (str): The URL of the video to be dubbed.
            - `source_language` (int): The ID of the source language.
            - `target_language` (int): The ID of the target language.
            - `polling_interval` (float, optional): The interval, in seconds, between each status
                check. Defaults to 30 seconds.
            - `debug` (bool, optional): If True, prints detailed debug information (task status and
                run ID) at each status check. Defaults to False.

        Returns:
            - DubbedRunInfo: A dictionary containing detailed information about the dubbed run.

        Raises:
            APIError: If the task status is neither "SUCCESS" nor "PENDING", or if the run ID is
            unavailable after the task completes.
        """

        # Initialize variables for the dubbing task status and task ID
        task: TaskStatus
        task_id: str

        print("Starting Dubbing")

        # Start the dubbing process
        response = self.start_dubbing(
            video_url=video_url,
            source_language=source_language,
            target_language=target_language,
        )

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
                raise APIError(
                    f"Dubbing Issue: {task['status']} for Run ID: {task['run_id']}"
                )

            # Wait for the specified polling interval before the next status check
            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            for _ in tqdm(
                range(math.ceil(polling_interval)),
                unit="s",
                desc=f"Waiting {polling_interval} seconds before checking status again",
            ):
                sleep(1)

        # Get the final status of the dubbing task
        task = self.get_task_status("dubbing", task_id)

        # If the run ID is None, raise an APIError
        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Return the dubbed run information
        return self.get_dubbed_run_info(task["run_id"])

    # ---------- TTS ---------- #

    def create_tts(
        self,
        /,
        text: str,
        voice_id: int,
        language: int,
        *,
        gender: Optional[Gender] = None,
        age: Optional[int] = None,
    ) -> TaskInfo:
        """
        Creates a text-to-speech (TTS) task with specified parameters.

        This method sends a POST request to the API to create a TTS task. The request includes
        mandatory parameters such as the text to be converted, the voice ID, and the language ID.

        Optionally, gender and age can be specified to further customize the voice profile used for
        the TTS task.

        Args:
            - `text` (str): The text to be converted into speech.
            - `voice_id` (int): The ID of the voice to be used for the TTS task.
            - `language` (int): The ID of the language in which the text is to be spoken.
            - `gender` (Optional[Gender], optional): The gender of the voice to be used.
                This should be an instance of the Gender enum if provided.
                Defaults to None, which means the API's default gender setting for the selected
                voice will be used.
            - `age` (Optional[int], optional): The age of the voice to be used. Defaults to None,
                which means the API's default age setting for the selected voice will be used.

        Returns:
            - TaskInfo: A dictionary containing information about the created TTS task, such as task
                ID and status.

        Raises:
            - TypeError: If the provided gender is not an instance of the Gender enum.
            - ValueError: If the language ID is not within the valid range (1 to 148).
            - SystemExit: If the API request fails (i.e., does not return a 200 status code), prints
                an error message along with the response details and exits the program.
        """

        # Validate the gender parameter
        if (gender is not None) and (not isinstance(gender, Gender)):
            raise TypeError("Gender must be an instance of Gender Enum.\n"
                            "Ensure 'Gender' Enum is imported.")

        # Validate the language ID range
        if not 1 <= language <= 148:
            raise ValueError("Language ID must be between 1 and 148")

        # Construct the API endpoint URL
        url: str = self.__create_api_endpoint("tts")

        # Prepare the data payload for the POST request
        data: dict = {
            "text": text,
            "voice_id": voice_id,
            "language": language,
        }

        # Include optional parameters in the payload if provided
        if gender is not None:
            data["gender"] = gender.value
        if age is not None:
            data["age"] = age

        # Set the request content type to JSON
        self.session.headers["Content-Type"] = "application/json"

        # Execute the POST request
        response: requests.Response = self.session.post(url=url, json=data)

        # Handle unsuccessful request
        if response.status_code != 200:
            print(f"Error: There was a {response.status_code} error with your POST request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the API response as a task information dictionary
        return response.json()


    def get_tts_status(self, /, task_id: str) -> TaskStatus:
        """
        Retrieves the status of a text-to-speech (TTS) task by its ID.

        This method is a convenience wrapper around `get_task_status` specifically for TTS tasks.

        It invokes `get_task_status` with the task type set to "tts" and the provided task ID,
        returning the current status of the TTS task.

        Args:
            - `task_id` (str): The unique identifier of the TTS task.

        Returns:
            - TaskStatus: A dictionary containing the status of the TTS task, including any relevant
            details provided by the API.
        """

        # Delegate to the generic get_task_status method, specifying the task type as "tts"
        return self.get_task_status("tts", task_id)


    def get_tts_result(
        self, /, run_id: int, *, output_directory: Optional[str] = "audio_tts"
    ) -> None:
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

        # Create the API endpoint URL using the provided run_id
        url: str = self.__create_api_endpoint(f"tts_result/{run_id}")

        # Send a GET request to the API endpoint
        response: requests.Response = self.session.get(url, stream=True)

        # Check for a successful response (status code 200)
        if response.status_code != 200:
            # Print error details and exit if the request was unsuccessful
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Check if the output directory exists
        if (output_directory is not None) and (not os.path.exists(output_directory)):
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


    def tts(
        self,
        /,
        text: str,
        voice_id: int,
        language: int,
        *,
        gender: Optional[Gender] = None,
        age: Optional[int] = None,
        polling_interval: float = 20,
        debug: bool = False,
        output_directory: str = "audio_tts",
    ) -> None:
        """
        Initiates a Text-to-Speech (TTS) process and monitors its progress until completion.

        This method creates a TTS task with the specified parameters, periodically checks the task's
        status until it is completed, and then retrieves the resulting audio file, saving it to the
        specified output directory.

        If the `debug` flag is set, it prints detailed information about the process to the console.

        Args:
            - `text` (str): The text to be converted into speech.
            - `voice_id` (int): The ID of the voice to be used for the TTS task.
            - `language` (int): The ID of the language in which the text is to be spoken.
            - `gender` (Optional[Gender], optional): The gender of the voice to be used.
                Defaults to None.
            - `age` (Optional[int], optional): The age of the voice to be used. Defaults to None.
            - `polling_interval` (float, optional): The interval, in seconds, between each status
                check. Defaults to 20 seconds.
            - `debug` (bool, optional): If True, prints debug information during the process.
                Defaults to False.
            - `output_directory` (str, optional): The directory where the resulting audio file will
                be saved. Defaults to "audio_tts".

        Returns:
            - None: This method does not return a value but saves the resulting audio file to the
                specified directory.

        Raises:
            - APIError: If the task status is neither "SUCCESS" nor "PENDING", or if the run ID is
                None after the task completes.
        """

        # Initialize task status and task ID
        task: TaskStatus
        task_id: str

        # Print debug information if debug is True
        if debug:
            print("Starting TTS process\n")

        # Create the TTS task
        response = self.create_tts(
            text=text, voice_id=voice_id, language=language, gender=gender, age=age
        )

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
                raise APIError(
                    f"Issue with TTS: {task['status']} for Run ID: {task['run_id']}"
                )

            # Wait for the specified polling interval before the next status check
            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            for _ in tqdm(
                range(math.ceil(polling_interval)),
                unit="s",
                desc=f"Waiting {polling_interval} seconds before checking status again",
            ):
                sleep(1)

        # Get the status of the TTS task
        task = self.get_task_status(task="tts", task_id=task_id)

        # Raise an error if the run ID is None
        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Get the TTS result and save it to the specified output directory
        return self.get_tts_result(run_id=task["run_id"], output_directory=output_directory)

    # ---------- Transcription ---------- #

    def create_transcription(
        self, /, audio_file: str, language: int
    ) -> TaskInfo:
        """
        Creates a transcription task for an audio file with the specified language.

        This method sends a POST request to the API to create a transcription task. The request
        includes the audio file and the language ID.

        The language ID must be within the valid range. If the request is successful, it returns the
        JSON response from the API, which contains details about the transcription task.

        Args:
            - `audio_file` (str): The path to the audio file to be transcribed.
            - `language` (int): The ID of the language in which the audio is spoken.

        Returns:
            - TaskInfo: A dictionary containing information about the created transcription task,
                such as task ID and status.

        Raises:
            - ValueError: If the language ID is not within the valid range.
            - FileNotFoundError: If the specified audio file does not exist.
            - SystemExit: If the API request fails (i.e., does not return a 200 status code),
                prints an error message along with the response details and exits the program.
        """

        # Validate the language ID range
        if not 1 <= language <= 148:
            raise ValueError("Language ID must be between 1 and 148")

        # Construct the API endpoint URL
        url: str = self.__create_api_endpoint("create_transcription")

        # Prepare the data payload with the language ID
        data: dict[str, int] = {"language": language}

        try:
            # Open the audio file in binary read mode
            with open(audio_file, "rb") as audio:
                # Make a POST request to the API with the audio file and language ID
                response: requests.Response = self.session.post(
                    url=url,
                    files={"file": audio},  # The audio file to be transcribed
                    data=data,  # Additional data including the language ID
                )

                # Check if the response status code indicates a successful request
                if response.status_code != 200:
                    print(f"Error: There was a {response.status_code} error"
                          " with your POST request.")
                    print("Response: "
                          f"{response.text if response.status_code == 500 else response.json()}")
                    print("Kindly fix the issue and try again.")
                    sys.exit(1)

                # Return the JSON response from the API
                return response.json()
        except FileNotFoundError:
            # Handle the case where the specified audio file does not exist
            print(
                "File not found."
                " Please enter a valid file path containing an audio file to send to the API."
            )
            sys.exit(1)


    def get_transcription_result(
        self, /, run_id: int, *, save_to_file: bool = False
    ) -> list[TranscriptionResult]:
        """
        Retrieves the transcription result for a given run ID and optionally saves it to a file.

        This method sends a GET request to the API to fetch the transcription result associated with
        the specified run ID.\\
        If the `save_to_file` parameter is set to True, the method also saves the transcription
        result to a local JSON file named `transcription_result_{run_id}.json`.

        The method returns the transcription result as a list of `TranscriptionResult` objects.

        Args:
            - `run_id` (int): The run ID of the transcription task whose result is to be fetched.
            - `save_to_file` (bool, optional): A flag indicating whether to save the transcription
                result to a file. Defaults to False.

        Returns:
            - list[TranscriptionResult]: A list of `TranscriptionResult` objects representing the
                transcription result.

        Raises:
            - SystemExit: If the API request fails (i.e., does not return a 200 status code), prints
                an error message along with the response details and exits the program.
        """

        # Construct the API endpoint URL using the provided run ID
        url: str = self.__create_api_endpoint(f"transcription_result/{run_id}")

        # Perform a GET request to the API endpoint
        response: requests.Response = self.session.get(url)

        # Check if the response status code indicates a successful request
        if response.status_code != 200:
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # If the save_to_file flag is True, save the transcription result to a JSON file
        if save_to_file:
            with open(
                f"transcription_result_{run_id}.json", "w", encoding="utf-8"
            ) as output_file:
                # Serialize JSON response with pretty printing and write it to the specified file
                json.dump(response.json(), output_file, indent=4)

        # Return the JSON response as a list of TranscriptionResult objects
        return response.json()


    def transcribe(
        self,
        /,
        audio_file: str,
        language: int,
        *,
        save_to_file: bool = False,
        polling_interval: float = 20,
        debug: bool = False,
    ) -> list[TranscriptionResult]:
        """
        Transcribes the given audio file to text in the specified language, with options to save and
        debug.

        This method initiates a transcription task for the provided audio file in the specified
        language. It periodically checks the status of the task at intervals defined by
        `polling_interval`.

        If `debug` is True, it prints the task's status during these checks.

        Once the task is completed successfully, it retrieves the transcription result.
        If `save_to_file` is True, the result is also saved to a local file.

        Args:
            - `audio_file` (str): The path to the audio file to be transcribed.
            - `language` (int): The ID of the language in which the audio is spoken.
            - `save_to_file` (bool, optional): If True, saves the transcription result to a file.
                Defaults to False.
            - `polling_interval` (float, optional): The time in seconds between status checks of the
                transcription task. Defaults to 20 seconds.
            - `debug` (bool, optional): If True, prints debug information during the transcription
                process. Defaults to False.

        Returns:
            - list[TranscriptionResult]: A list of transcription results.

        Raises:
            - APIError: If the task status is neither "SUCCESS" nor "PENDING", or if the run ID is
                None after the task completes.
        """

        task: TaskStatus
        task_id: str

        print("Starting Transcription")

        # Create a new transcription task with the specified audio file and language
        response = self.create_transcription(audio_file, language)

        print(f"Transcription Task Started: {response}")

        # Extract the task ID from the response
        task_id = response["task_id"]

        while True:
            # Check the current status of the transcription task
            task = self.get_task_status("transcription", task_id)

            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")

            # Exit the loop if the task is successfully completed
            if task["status"] == "SUCCESS":
                break

            # Raise an error if the task status indicates a failure
            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(
                    f"Transcription Issue: {task['status']} for Run ID: {task['run_id']}"
                )

            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            # Wait for the specified polling interval with a progress bar
            for _ in tqdm(
                range(math.ceil(polling_interval)),
                unit="s",
                desc=f"Waiting {polling_interval} seconds before checking status again",
            ):
                sleep(1)

        # Retrieve the final task status to get the run ID
        task = self.get_task_status("transcription", task_id)

        if task["run_id"] is None:
            # Raise an error if the run ID is missing
            raise APIError("Run ID is None")

        # Retrieve and return the transcription result
        return self.get_transcription_result(
            run_id=task["run_id"], save_to_file=save_to_file
        )

    # ---------- Translation ---------- #

    def create_translation(
        self,
        /,
        text: str,
        source_language: int,
        target_language: int,
        age: int,
        *,
        formality: Optional[int] = None,
        gender: Optional[Gender] = None,
    ) -> TaskInfo:
        """
        Creates a translation request and sends it to the translation API.

        This method constructs a translation request with mandatory and optional parameters,
        validates the parameters, and sends the request to the specified translation API endpoint.
        It returns the response in JSON format.

        Parameters:
            - `source_language` (int): The ID of the source language.
            - `target_language` (int): The ID of the target language.
            - `text` (str): The text to be translated.
            - `age` (int): The age of the text's intended audience.
            - `formality` (int, optional): The formality level of the translation, if applicable.
            - `gender` (Gender, optional): The gender of the text's intended audience, if applicable

        Returns:
            - dict[str, str]: The response from the translation API in JSON format.

        Raises:
            - ValueError: If any of the language IDs or formality values are out of their valid
                          range.

        Note:
            - The `source_language` and `target_language` IDs must be within the valid range.
            - The `formality` parameter, if provided, must be either 1 or 2.
            - The `gender` parameter, if provided, must be an instance of the `Gender` enum.
        """

        # Validate source language ID
        if not 1 <= source_language <= 148:
            raise ValueError(
                "create_translation: Source Language must be an integer"
                "value between 1 and 148. To know more, call"
                "the 'get_languages(\"source\")' function"
            )

        # Validate target language ID
        if not 1 <= target_language <= 148:
            raise ValueError(
                "create_translation: Target Language must be an integer value"
                "between 1 and 148. To know more, call the"
                "'get_languages(\"target\")' function"
            )

        # Validate formality, if provided
        if (formality is not None) and (formality not in {1, 2}):
            raise ValueError("create_translation: formality must be one of {1, 2}")

        # Check if the gender is an instance of the Gender Enum
        if (gender is not None) and (not isinstance(gender, Gender)):
            raise TypeError(
                "Gender must be an instance of Gender Enum.\n",
                "Make sure you have imported the 'Gender' Enum",
            )

        # Construct the API endpoint URL
        url: str = self.__create_api_endpoint("create_translation")

        # Set the content type for the request
        self.session.headers["Content-Type"] = "application/json"

        # Construct the data payload for the POST request
        data: ExtendedTranslationData = {
            "source_language": source_language,
            "target_language": target_language,
            "text": text,
        }

        # Add optional parameters to the payload, if provided
        if age is not None:
            data["age"] = age
        if formality is not None:
            data["formality"] = formality
        if gender is not None:
            data["gender"] = gender.value

        # Send the POST request to the API
        response: requests.Response = self.session.post(url=url, json=data)

        # Check for successful response
        if response.status_code != 200:
            print(f"Error: There was a {response.status_code} error with your POST request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the JSON response
        return response.json()


    def get_translation_status(self, /, task_id: str) -> TaskStatus:
        """Retrieves the status of a translation task by its ID.

        This method is a convenience wrapper around `get_task_status` specifically for translation
        tasks.\\
        It invokes `get_task_status` with the task type set to "translation" and the provided
        task ID, returning the current status of the translation task.

        Args:
            - `task_id` (str): The unique identifier of the translation task.

        Returns:
            - TaskStatus: A dictionary containing the status of the translation task, including any
                relevant details provided by the API.
        """

        return self.get_task_status("translation", task_id)


    def get_translation_result(
        self, /, run_id: int, *, save_to_file: bool = False
    ) -> TranslationResult:
        """
        Retrieves the translation result for a given run ID.

        Args:
            `run_id` (int): The ID of the translation run.
            `save_to_file` (bool): Whether to save the result to a file. Defaults to False.

        Returns:
            TranslationResult: The translation result as a dictionary.
        """

        # Create the URL for the API endpoint
        url: str = self.__create_api_endpoint(f"translation_result/{run_id}")

        # Send a GET request to the API endpoint and get the response
        response: requests.Response = self.session.get(url)

        if response.status_code != 200:
            print(f"Error: There was a {response.status_code} error with your GET request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # If save_to_file is True, write the translation result to a file
        if save_to_file:
            with open(f"translation_result_{run_id}.txt", "w", encoding="utf-8") as file:
                file.writelines([
                    "Camb AI Translation Result\n",
                    f"Run ID: {run_id}\n"
                ])
                file.write(response.json()["text"])

        return response.json()


    def translate(
        self,
        /,
        text: str,
        source_language: int,
        target_language: int,
        age: int,
        *,
        formality: Optional[int] = None,
        gender: Optional[Gender] = None,
        polling_interval: float = 10,
        save_to_file: bool = False,
        debug: bool = False,
    ) -> TranslationResult:
        """
        Translates text from a source language to a target language, with optional parameters to
        customize the request.

        This method initiates a translation task, polls for its completion, and retrieves the
        result.\\
        It supports customization of the translation through parameters like age, formality, and
        gender.\\
        It also allows for the result to be saved to a file if desired.

        Parameters:
            - `text` (str): The text to be translated.
            - `source_language` (int): The language code of the source text.
            - `target_language` (int): The language code for the translation output.
            - `age` (int): Age parameter to customize the translation request.
            - `formality` (int, optional): Optional formality level for the translation.
            - `gender` (Gender, optional): Optional gender to customize the translation request.
            - `polling_interval` (float): Time in seconds between status checks of the translation
                task. Defaults to 10.
            - `save_to_file` (bool): Flag to save the translation output as a file. Defaults to
                False.
            - `debug` (bool): Enables detailed logging if set to True. Defaults to False.

        Returns:
            - TranslationResult: The result of the translation process, including any file
                information if saved.

        Raises:
            - APIError: If the task fails or if there is an issue retrieving the result.
        """

        task: TaskStatus
        task_id: str

        print("Starting Translation")

        # Initiate the translation task with the provided parameters
        response = self.create_translation(
            text, source_language, target_language, age, formality=formality, gender=gender
        )

        print(f"Translation Task Started: {response}")

        task_id = response["task_id"]

        while True:
            # Check the current status of the translation task
            task = self.get_task_status("translation", task_id)

            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")

            # Exit the loop if the task is successfully completed
            if task["status"] == "SUCCESS":
                break

            # Raise an error if the task status indicates a failure
            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(f"Translation Issue: {task['status']} for Run ID: {task['run_id']}")

            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            # Wait for the specified polling interval before checking the task status again
            for _ in tqdm(
                range(math.ceil(polling_interval)),
                unit="s",
                desc=f"Waiting {polling_interval} seconds before checking status again",
            ):
                sleep(1)

        task = self.get_task_status("translation", task_id)

        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Retrieve and return the final translation result
        return self.get_translation_result(task["run_id"], save_to_file=save_to_file)

    # ---------- Translated TTS ---------- #

    def create_translated_tts(
        self,
        /,
        text: str,
        voice_id: int,
        source_language: int,
        target_language: int,
        *,
        age: Optional[int] = None,
        formality: Optional[int] = None,
        gender: Optional[Gender] = None,
    ) -> TaskInfo:
        """
        Creates a translation with Text-to-Speech (TTS) from source to target language with optional
        voice customization.

        This method translates the given text from the source language to the target language and
        synthesizes the translation into speech using the specified voice ID.\\
        Optional parameters allow for customization of the TTS output, including the age, formality,
        and gender of the voice.

        Args:
            - `text` (str): The text to be translated and synthesized.
            - `voice_id` (int): The ID of the voice to be used for TTS.
            - `source_language` (int): The ID of the source language.
            - `target_language` (int): The ID of the target language.
            - `age` (int, optional): The desired age group for the TTS voice.
            - `formality` (int, optional): The desired level of formality for the TTS
                voice.
            - `gender` (Gender, optional): The desired gender for the TTS voice.

        Returns:
            - TaskInfo: A dictionary containing information about the TTS task, including status and
                any results.

        Raises:
            - ValueError: If the source or target language IDs are not within the valid range
                (1-148).
            - ValueError: If the formality value is provided but is not one of the valid options
                (1, 2).
            - TypeError: If the gender is provided but is not an instance of the Gender Enum.
        """

        # Validate source language ID
        if not 1 <= source_language <= 148:
            raise ValueError(
                "create_translated_tts: Source Language must be an integer"
                "value between 1 and 148. To know more, call"
                "the 'get_languages(\"source\")' function"
            )

        # Validate target language ID
        if not 1 <= target_language <= 148:
            raise ValueError(
                "create_translated_tts: Target Language must be an integer value"
                "between 1 and 148. To know more, call the"
                "'get_languages(\"target\")' function"
            )

        # Validate formality, if provided
        if (formality is not None) and (formality not in {1, 2}):
            raise ValueError("create_translated_tts: formality must be one of {1, 2}")

        # Check if the gender is an instance of the Gender Enum
        if (gender is not None) and (not isinstance(gender, Gender)):
            raise TypeError(
                "Gender must be an instance of Gender Enum.\n",
                "Make sure you have imported the 'Gender' Enum",
            )

        # Construct the API endpoint URL
        url: str = self.__create_api_endpoint("create_translated_tts")

        # Set the content type for the request
        self.session.headers["Content-Type"] = "application/json"

        # Prepare the data payload for the POST request
        data: ExtendedTranslationTTSData = {
            "text": text,
            "voice_id": voice_id,
            "source_language": source_language,
            "target_language": target_language,
        }

        # Add optional parameters to the data payload if provided
        if age is not None:
            data["age"] = age
        if formality is not None:
            data["formality"] = formality
        if gender is not None:
            data["gender"] = gender

        # Make the POST request to the API endpoint
        response: requests.Response = self.session.post(url=url, json=data)

        # Check for successful response
        if response.status_code != 200:
            print(f"Error: There was a {response.status_code} error with your POST request.")
            print(f"Response: {response.text if response.status_code == 500 else response.json()}")
            print("Kindly fix the issue and try again.")
            sys.exit(1)

        # Return the Task Info
        return response.json()


    def get_translated_tts_status(self, /, task_id: str) -> TaskStatus:
        """Retrieves the status of a translation task by its ID.

        This method is a convenience wrapper around `get_task_status` specifically for translation
        TTS tasks.\\
        It invokes `get_task_status` with the task type set to "translation_tts" and the provided
        task ID, returning the current status of the translation task.

        Args:
            - `task_id` (str): The unique identifier of the TTS translation task whose status is
                being queried.

        Returns:
            - TaskStatus: An object containing the current status of the task, including whether it
                is pending, in progress, or completed.
        """

        return self.get_task_status("translated_tts", task_id)


    def get_translated_tts_result(
        self,
        /,
        run_id: int,
        *,
        output_directory: str = "audio_tts",
        save_to_file: bool = False,
    ) -> TranslationResult:
        """
        Retrieves the result of a translated Text-to-Speech (TTS) task and optionally saves the
        audio file.

        This method fetches the result of a TTS translation task using its run ID.\\
        It can also save the resulting audio file to a specified directory.
        The method first retrieves the TTS audio result and then fetches the translation text
        result.

        Args:
            - `run_id` (int): The unique identifier of the TTS translation task.
            - `output_directory` (str, optional): The directory where the audio file will be saved
                if `save_to_file` is True. Defaults to "audio_tts".
            - `save_to_file` (bool, optional): If True, the audio file will be saved to the
                specified `output_directory`. Defaults to False.

        Returns:
            - TranslationResult: An object containing the translation text result and, if requested,
                the path to the saved audio file.
        """

        # Retrieve and optionally save the TTS audio result
        self.get_tts_result(run_id, output_directory=output_directory)

        # Retrieve and return the translation text result,
        # including the path to the saved audio file if applicable
        return self.get_translation_result(run_id, save_to_file=save_to_file)


    def translate_tts(
        self,
        /,
        text: str,
        voice_id: int,
        source_language: int,
        target_language: int,
        *,
        age: Optional[int] = None,
        formality: Optional[int] = None,
        gender: Optional[Gender] = None,
        output_directory: str = "audio_tts",
        save_to_file: bool = False,
        polling_interval: float = 20,
        debug: bool = False
    ) -> TranslationResult:
        """
        Translates text to speech in a target language and optionally saves the audio file.

        This method initiates a translated text-to-speech (TTS) task, polls for its completion,
        and retrieves the result. It supports customization of the voice through parameters like
        age, formality, and gender. It also allows for the audio to be saved to a specified
        directory.

        Parameters:
            - `text` (str): The text to be translated and converted to speech.
            - `voice_id` (int): Identifier for the voice type to be used in the TTS.
            - `source_language` (int): Language code of the input text.
            - `target_language` (int): Language code for the translation and TTS output.
            - `age` (int, optional): Optional age parameter to customize the voice.
            - `formality` (int, optional): Optional formality level for the voice.
            - `gender` (Gender, optional): Optional gender to customize the voice.
            - `output_directory` (str): Directory where the audio file will be saved. Defaults to
                "audio_tts".
            - `save_to_file` (bool): Flag to save the audio output as a file. Defaults to False.
            - `polling_interval` (float): Time in seconds between status checks of the TTS task.
                Defaults to 20.
            - `debug` (bool): Enables detailed logging if set to True. Defaults to False.

        Returns:
            - TranslationResult: The result of the translation and TTS process, including any audio
                file information.

        Raises:
            - APIError: If the task fails or if there is an issue retrieving the result.
        """

        task: TaskStatus
        task_id: str

        print("Starting Translated TTS")

        # Create a translated TTS task with the provided parameters
        response = self.create_translated_tts(
            text, voice_id, source_language, target_language,
            age=age, formality=formality, gender=gender
        )

        print(f"Translated TTS Task Started: {response}")

        task_id = response["task_id"]

        # Poll for task completion, with optional debug logging
        while True:
            task = self.get_task_status("translated_tts", task_id)

            if debug:
                print(f"Task Status: {task['status']}, Run ID: {task['run_id']}")

            if task["status"] == "SUCCESS":
                break

            if task["status"] not in ["SUCCESS", "PENDING"]:
                raise APIError(f"Dubbing Issue: {task['status']} for Run ID: {task['run_id']}")

            if debug:
                print(f"Sleeping for {polling_interval} seconds")

            # Wait for the specified polling interval before checking the task status again
            for _ in tqdm(
                range(math.ceil(polling_interval)),
                unit="s",
                desc=f"Waiting {polling_interval} seconds before checking status again",
            ):
                sleep(1)

        task = self.get_task_status("translated_tts", task_id)

        if task["run_id"] is None:
            raise APIError("Run ID is None")

        # Retrieve and return the final translated TTS result
        return self.get_translated_tts_result(
            task["run_id"], output_directory=output_directory, save_to_file=save_to_file
        )
