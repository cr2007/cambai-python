<!-- omit from toc -->
# Camb AI API Wrapper

This is a Python wrapper for the CambAI API. It is designed to make it easy to interact with the CambAI API from Python.

> [!IMPORTANT]
> This library is still in active development.
> There will be some fixes and improvements to be made.

<!-- omit from toc -->
## Index

- [Installation](#installation)
- [Usage](#usage)
  - [TTS](#tts)
  - [Dubbing](#dubbing)

## Installation

To install the CambAI API Wrapper, you can use `pip` to install:

```bash
pip install cambai
```

## Usage

### TTS

```python
from cambai import CambAI, Gender
from dotenv import load_dotenv

load_dotenv()

def main():
    client = CambAI()
    client.get_all_voices(write_to_file=True) # Set 'write_to_file' to False if you don't want to view the list of voices in a JSON file

    client.tts(
        text="Hello, World!",
        language=1,
        gender=Gender.MALE,
        age=25,
        voice_id=<enter-voice-id>,
        debug=True,
        polling_interval=3
    )

if __name__ == "__main__":
    main()
```

Output:
```
Voices written to voices.json
Starting TTS process

TTS Task Started: {'task_id': 'de2668c5-b975-4887-8738-3afdf9f5cea6'}

TTS Status: PENDING, Run ID: None
Sleeping for 3 seconds
Waiting 3 seconds before checking status again: 100%|████████████| 3/3 [00:03<00:00,  1.00s/s]
TTS Status: PENDING, Run ID: None
Sleeping for 3 seconds
Waiting 3 seconds before checking status again: 100%|████████████| 3/3 [00:03<00:00,  1.00s/s]
...
TTS Status: SUCCESS, Run ID: 12012

TTS audio written to 'audio_tts/tts_stream_12012.wav'
```

### Dubbing

```python
from cambai import CambAI
from dotenv import load_dotenv
from rich import print

load_dotenv()

def main():
    print("Starting...")
    client = CambAI()

    ## Dubbing example

    # You can get the list of source and target languages by calling the 'get_languages' method
    client.get_languages("source", write_to_file=True)

    print("Sending URL")
    values = client.dub(
        video_url="", # Insert any public accessible URL here (e.g. YouTube, Vimeo, etc.)
        source_language=1,  # English (United States)
        target_language=76, # French (France)
        debug=True,         # Set to False to not view the debug print statements
        polling_interval=10 # Set the interval to check the status of the dubbing task
    )

    print(f"Output Video URL: {values["video_url"]}")
    print(f"Output Audio URL: {values["audio_url"]}")

if __name__ == "__main__":
    main()
```
