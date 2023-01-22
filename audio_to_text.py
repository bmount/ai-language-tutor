from io import BytesIO
from tempfile import mkstemp
import os
import base64
import whisper
from abc import ABC
from io import BytesIO
import base64
import os
from google.cloud import speech

import banana_dev as banana

class Transcriber(ABC):
    def transcribe(self, audio_path: str):
        raise NotImplementedError

class WhisperTranscriber(Transcriber):
    def __init__(self, model="base"):
        self.model = whisper.load(model)

    def transcribe(self, audio_path: str):
        return self.model.transcribe(audio_path)

class GCPTranscriber(Transcriber):
    def __init__(self, language_code="en-US"):
        self.language_code = language_code
        pass

    def transcribe(self, speech_file):
        """Transcribe the given audio file asynchronously."""

        client = speech.SpeechClient()

        with open(speech_file, "rb") as audio_file:
            content = audio_file.read()

        """
        Note that transcription is limited to a 60 seconds audio file.
        Use a GCS file for audio longer than 1 minute.
        """
        audio = speech.RecognitionAudio(content=content)

        config = speech.RecognitionConfig(
            language_code=self.language_code,
        )


        operation = client.long_running_recognize(config=config, audio=audio)

        print("Waiting for operation to complete...")
        response = operation.result(timeout=90)

        return response.results

class BananaTranscriber(Transcriber):
    def __init__(self):
        self.api_key = os.getenv('BANANADEV_API_KEY')
        self.model_id = os.getenv('BANANADEV_WHISPER_MODEL_ID')

    def transcribe(self, wav_path):
        with open(wav_path,'rb') as file:
            wav_buffer = BytesIO(file.read())
        wav_b64 = base64.b64encode(wav_buffer.getvalue()).decode("ISO-8859-1")
        model_payload = {"wav_b64": wav_b64}

        #use following to call deployed model on banana, model_payload is same as above
        out = banana.run(self.api_key, self.model_id, model_payload)
        return out.get('modelOutputs')[0]


# optionally, run locally:
#model = whisper.load_model("base")
#model = whisper.load_model("large-v2")

