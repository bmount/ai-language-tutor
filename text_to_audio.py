import google.cloud.texttospeech as tts
import os
from tempfile import mkstemp
import secrets

from config import AUDIO_DIR

# follow: https://codelabs.developers.google.com/codelabs/cloud-text-speech-python3 to set up credentials


def unique_languages_from_voices(voices):
    language_set = set()
    for voice in voices:
        for language_code in voice.language_codes:
            language_set.add(language_code)
    return language_set


def list_languages():
    client = tts.TextToSpeechClient()
    response = client.list_voices()
    languages = unique_languages_from_voices(response.voices)

    print(f" Languages: {len(languages)} ".center(60, "-"))
    for i, language in enumerate(sorted(languages)):
        print(f"{language:>10}", end="\n" if i % 5 == 4 else "")



def list_voices(language_code=None):
    client = tts.TextToSpeechClient()
    response = client.list_voices(language_code=language_code)
    voices = sorted(response.voices, key=lambda voice: voice.name)

    print(f" Voices: {len(voices)} ".center(60, "-"))
    for voice in voices:
        languages = ", ".join(voice.language_codes)
        name = voice.name
        gender = tts.SsmlVoiceGender(voice.ssml_gender).name
        rate = voice.natural_sample_rate_hertz
        print(f"{languages:<8} | {name:<24} | {gender:<8} | {rate:,} Hz")
    return voices

def default_voice_name_for_language(language):
    language = language.lower()
    best = dict(
        english="en-AU-Neural2-A",
        italian="it-IT-Neural2-A",
        french="fr-CA-Neural2-A",
        german="de-DE-Neural2-D",
        spanish="es-US-Neural2-A",
        japanese="ja-JP-Neural2-B",
    )
    return best.get(language, 'en-AU-Neural2-A')


def text_to_wav(voice_name: str, text: str):
    language_code = 'en-GB' if not voice_name else "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input, voice=voice_params, audio_config=audio_config
    )

    tmp_path = f"{AUDIO_DIR}/{secrets.token_hex(32)}.wav"
    with open(tmp_path, "wb") as out:
        out.write(response.audio_content)
    return tmp_path


if __name__ == '__main__':
    list_languages()
    list_voices()
