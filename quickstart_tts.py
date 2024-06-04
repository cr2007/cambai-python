from dotenv import load_dotenv
from cambai import CambAI, Gender

load_dotenv()

def main():
    client = CambAI()
    client.get_all_voices(write_to_file=True) # Set 'write_to_file' to False if you don't want to view the list of voices in a JSON file

    client.tts(
        text="Hello, World!",
        language=1,
        gender=Gender.MALE,
        age=25,
        voice_id=<enter-voice-id>, # You can get the voice ID by calling the 'get_all_voices' method
        debug=True,
        polling_interval=3
    )

if __name__ == "__main__":
    main()
