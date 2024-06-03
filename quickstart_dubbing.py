from cambai import CambAI
from dotenv import load_dotenv
from rich import print

load_dotenv()

def main():
    print("Starting...")
    client = CambAI()

    # You can get the list of source and target languages by calling the 'get_languages' method
    client.get_languages("source", write_to_file=True) # Gets the source languages and writes them to a file

    print("Sending URL")
    values = client.dub(
        video_url="https://youtu.be/jNQXAC9IVRw", # Me at the Zoo (1st YouTube video)
        source_language=1,  # English (United States)
        target_language=76, # French (France)
        debug=True,         # Set to False to not view the debug print statements
        polling_interval=30 # Set the interval to check the status of the dubbing task
    )

    print(f"Output Video URL: {values["video_url"]}")
    print(f"Output Audio URL: {values["audio_url"]}")

if __name__ == "__main__":
    main()
