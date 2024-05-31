# Camb AI API Wrapper

This is a Python wrapper for the CambAI API. It is designed to make it easy to interact with the CambAI API from Python.

> [!IMPORTANT]
> This library is still is still in active development.
> There will still be some fixes and improvements to be made.

## Installation

> [!WARNING]
> `pip install` has not been setup just yet. Will be updated once ready

~~To install the CambAI API Wrapper, you can use `pip` to install:~~

```bash
pip install camb-ai-pip
```

# To Do

- [X] Dubbing
- [X] Get Source/Target Langauges
- [X] Get Dubbing Status
- [X] Get Dubbed Run Details
- [X] TTS
- [ ] Testing

## Usage

### TTS

```python
from cambai import CambAI, Gender
from dotenv import load_dotenv

load_dotenv()

def main():
    client = CambAI()
    print(client.get_all_voices())

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
[
    {'id': 8913, 'voice_name': 'Monaco'},
    {'id': 8914, 'voice_name': 'Billie'},
    {'id': 8915, 'voice_name': 'Noor'},
    {'id': 8916, 'voice_name': 'Logan'}
]
Starting TTS process
TTS Task Started: {'task_id': 'c8b8e3cd-ad17-4458-83ad-349432da117b'}
TTS Status: PENDING, Run ID: None
Sleeping for 3 seconds
TTS Status: PENDING, Run ID: None
Sleeping for 3 seconds
TTS Status: PENDING, Run ID: None
Sleeping for 3 seconds
TTS Status: SUCCESS, Run ID: 11768
File directory does not exist. Creating directory...
TTS audio written to tts_stream_11768.wav
```
