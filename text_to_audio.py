import google.cloud.texttospeech as tts
import os
from tempfile import mkstemp
import secrets

from config import AUDIO_DIR, logger

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
    return languages


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

TRANSCRIBE_LANGUAGES = {
    "en": "english",
    "zh": "chinese",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "ko": "korean",
    "fr": "french",
    "ja": "japanese",
    "pt": "portuguese",
    "tr": "turkish",
    "pl": "polish",
    "ca": "catalan",
    "nl": "dutch",
    "ar": "arabic",
    "sv": "swedish",
    "it": "italian",
    "id": "indonesian",
    "hi": "hindi",
    "fi": "finnish",
    "vi": "vietnamese",
    "he": "hebrew",
    "uk": "ukrainian",
    "el": "greek",
    "ms": "malay",
    "cs": "czech",
    "ro": "romanian",
    "da": "danish",
    "hu": "hungarian",
    "ta": "tamil",
    "no": "norwegian",
    "th": "thai",
    "ur": "urdu",
    "hr": "croatian",
    "bg": "bulgarian",
    "lt": "lithuanian",
    "la": "latin",
    "mi": "maori",
    "ml": "malayalam",
    "cy": "welsh",
    "sk": "slovak",
    "te": "telugu",
    "fa": "persian",
    "lv": "latvian",
    "bn": "bengali",
    "sr": "serbian",
    "az": "azerbaijani",
    "sl": "slovenian",
    "kn": "kannada",
    "et": "estonian",
    "mk": "macedonian",
    "br": "breton",
    "eu": "basque",
    "is": "icelandic",
    "hy": "armenian",
    "ne": "nepali",
    "mn": "mongolian",
    "bs": "bosnian",
    "kk": "kazakh",
    "sq": "albanian",
    "sw": "swahili",
    "gl": "galician",
    "mr": "marathi",
    "pa": "punjabi",
    "si": "sinhala",
    "km": "khmer",
    "sn": "shona",
    "yo": "yoruba",
    "so": "somali",
    "af": "afrikaans",
    "oc": "occitan",
    "ka": "georgian",
    "be": "belarusian",
    "tg": "tajik",
    "sd": "sindhi",
    "gu": "gujarati",
    "am": "amharic",
    "yi": "yiddish",
    "lo": "lao",
    "uz": "uzbek",
    "fo": "faroese",
    "ht": "haitian creole",
    "ps": "pashto",
    "tk": "turkmen",
    "nn": "nynorsk",
    "mt": "maltese",
    "sa": "sanskrit",
    "lb": "luxembourgish",
    "my": "myanmar",
    "bo": "tibetan",
    "tl": "tagalog",
    "mg": "malagasy",
    "as": "assamese",
    "tt": "tatar",
    "haw": "hawaiian",
    "ln": "lingala",
    "ha": "hausa",
    "ba": "bashkir",
    "jw": "javanese",
    "su": "sundanese",
}

TRANSCRIBE_CODES = {v: k for k, v in TRANSCRIBE_LANGUAGES.items()}

SYNTHESIZE_CODES = {"nl-BE": "Flemish Dutch", "cs-CZ": "Czech", "ml-IN": "Malayalam",
    "ro-RO": "Romanian", "es-ES": "European Spanish", "ru-RU": "Russian", "da-DK": "Danish",
    "ko-KR": "Korean", "cmn-CN": "Mandarin Chinese", "nl-NL": "Dutch", "hu-HU": "Hungarian",
    "en-AU": "Australian English", "it-IT": "Italian", "sk-SK": "Slovak", "tr-TR": "Turkish",
    "ta-IN": "Tamil", "fil-PH": "Filipino", "es-US": "American Spanish", "ca-ES": "Catalan",
    "kn-IN": "Kannada", "mr-IN": "Marathi", "ms-MY": "Malay", "af-ZA": "Afrikaans", "fi-FI": "Finnish",
    "el-GR": "Greek", "lv-LV": "Latvian", "nb-NO": "Norwegian Bokmål", "uk-UA": "Ukrainian",
    "yue-HK": "Cantonese", "en-IN": "Indian English", "th-TH": "Thai", "fr-FR": "French",
    "is-IS": "Icelandic", "cmn-TW": "Taiwanese Mandarin", "sv-SE": "Swedish", "hi-IN": "Hindi",
    "vi-VN": "Vietnamese", "en-GB": "British English", "te-IN": "Telugu", "en-US": "American English",
    "pa-IN": "Punjabi", "ja-JP": "Japanese", "pl-PL": "Polish", "pt-PT": "European Portuguese",
    "bg-BG": "Bulgarian", "pt-BR": "Brazilian Portuguese", "gu-IN": "Gujarati", "id-ID": "Indonesian",
    "sr-RS": "Serbian", "ar-XA": "Arabic", "de-DE": "German", "fr-CA": "Canadian French", "bn-IN": "Bengali"}


PREFERRED_MODELS = {
    'af-ZA': {'male': None, 'female': 'af-ZA-Standard-A'},
    'ar-XA': {'male': 'ar-XA-Wavenet-B', 'female': 'ar-XA-Wavenet-A'},
    'bg-BG': {'male': None, 'female': 'bg-BG-Standard-A'},
    'bn-IN': {'male': 'bn-IN-Wavenet-B', 'female': 'bn-IN-Wavenet-A'},
    'ca-ES': {'male': None, 'female': 'ca-ES-Standard-A'},
    'cmn-CN': {'male': 'cmn-CN-Wavenet-B', 'female': 'cmn-CN-Wavenet-A'},
    'cmn-TW': {'male': 'cmn-TW-Wavenet-B', 'female': 'cmn-TW-Wavenet-A'},
    'cs-CZ': {'male': None, 'female': 'cs-CZ-Wavenet-A'},
    'da-DK': {'male': 'da-DK-Wavenet-C', 'female': 'da-DK-Wavenet-A'},
    'de-DE': {'male': 'de-DE-Neural2-D', 'female': 'de-DE-Neural2-F'},
    'el-GR': {'male': None, 'female': 'el-GR-Wavenet-A'},
    'en-AU': {'male': 'en-AU-Neural2-B', 'female': 'en-AU-Neural2-A'},
    'en-GB': {'male': 'en-GB-Neural2-B', 'female': 'en-GB-Neural2-A'},
    'en-IN': {'male': 'en-IN-Wavenet-B', 'female': 'en-IN-Wavenet-A'},
    'en-US': {'male': 'en-US-Neural2-A', 'female': 'en-US-Neural2-C'},
    'es-ES': {'male': 'es-ES-Neural2-B', 'female': 'es-ES-Neural2-A'},
    'es-US': {'male': 'es-US-Neural2-B', 'female': 'es-US-Neural2-A'},
    'fi-FI': {'male': None, 'female': 'fi-FI-Wavenet-A'},
    'fil-PH': {'male': 'fil-PH-Wavenet-C', 'female': 'fil-PH-Wavenet-A'},
    'fr-CA': {'male': 'fr-CA-Neural2-B', 'female': 'fr-CA-Neural2-A'},
    'fr-FR': {'male': 'fr-FR-Neural2-B', 'female': 'fr-FR-Neural2-A'},
    'gu-IN': {'male': 'gu-IN-Wavenet-B', 'female': 'gu-IN-Wavenet-A'},
    'hi-IN': {'male': 'hi-IN-Wavenet-B', 'female': 'hi-IN-Wavenet-A'},
    'hu-HU': {'male': None, 'female': 'hu-HU-Wavenet-A'},
    'id-ID': {'male': 'id-ID-Wavenet-B', 'female': 'id-ID-Wavenet-A'},
    'is-IS': {'male': None, 'female': 'is-IS-Standard-A'},
    'it-IT': {'male': 'it-IT-Neural2-C', 'female': 'it-IT-Neural2-A'},
    'ja-JP': {'male': 'ja-JP-Neural2-C', 'female': 'ja-JP-Neural2-B'},
    'kn-IN': {'male': 'kn-IN-Wavenet-B', 'female': 'kn-IN-Wavenet-A'},
    'ko-KR': {'male': 'ko-KR-Wavenet-C', 'female': 'ko-KR-Wavenet-A'},
    'lv-LV': {'male': 'lv-LV-Standard-A', 'female': None},
    'ml-IN': {'male': 'ml-IN-Wavenet-B', 'female': 'ml-IN-Wavenet-A'},
    'mr-IN': {'male': 'mr-IN-Wavenet-B', 'female': 'mr-IN-Wavenet-A'},
    'ms-MY': {'male': 'ms-MY-Wavenet-B', 'female': 'ms-MY-Wavenet-A'},
    'nb-NO': {'male': 'nb-NO-Wavenet-B', 'female': 'nb-NO-Wavenet-A'},
    'nl-BE': {'male': 'nl-BE-Wavenet-B', 'female': 'nl-BE-Wavenet-A'},
    'nl-NL': {'male': 'nl-NL-Wavenet-B', 'female': 'nl-NL-Wavenet-A'},
    'pa-IN': {'male': 'pa-IN-Wavenet-B', 'female': 'pa-IN-Wavenet-A'},
    'pl-PL': {'male': 'pl-PL-Wavenet-B', 'female': 'pl-PL-Wavenet-A'},
    'pt-BR': {'male': 'pt-BR-Neural2-B', 'female': 'pt-BR-Neural2-A'},
    'pt-PT': {'male': 'pt-PT-Wavenet-B', 'female': 'pt-PT-Wavenet-A'},
    'ro-RO': {'male': None, 'female': 'ro-RO-Wavenet-A'},
    'ru-RU': {'male': 'ru-RU-Wavenet-B', 'female': 'ru-RU-Wavenet-A'},
    'sk-SK': {'male': None, 'female': 'sk-SK-Wavenet-A'},
    'sr-RS': {'male': None, 'female': 'sr-rs-Standard-A'},
    'sv-SE': {'male': 'sv-SE-Wavenet-C', 'female': 'sv-SE-Wavenet-A'},
    'ta-IN': {'male': 'ta-IN-Wavenet-B', 'female': 'ta-IN-Wavenet-A'},
    'te-IN': {'male': 'te-IN-Standard-B', 'female': 'te-IN-Standard-A'},
    'th-TH': {'male': None, 'female': 'th-TH-Standard-A'},
    'tr-TR': {'male': 'tr-TR-Wavenet-B', 'female': 'tr-TR-Wavenet-A'},
    'uk-UA': {'male': None, 'female': 'uk-UA-Wavenet-A'},
    'vi-VN': {'male': 'vi-VN-Wavenet-B', 'female': 'vi-VN-Wavenet-A'},
    'yue-HK': {'male': 'yue-HK-Standard-B', 'female': 'yue-HK-Standard-A'}
}

fully_supported = set([i for i in SYNTHESIZE_CODES.keys() if i.split('-')[0] in TRANSCRIBE_LANGUAGES])

def prompt_supported_languages(plain = False):
    if plain:
        return [v for k, v in SYNTHESIZE_CODES.items() if k in fully_supported]
    return ' '.join([f'The code for {v} is {k}.' for k, v in SYNTHESIZE_CODES.items() if k in fully_supported])

def find_best_voice(ua_tag, gender='female'):
    """Find the best voice synthesis model for the given language/gender pair."""
    logger.debug(f'Finding best voice for {ua_tag}')
    available = PREFERRED_MODELS.get(ua_tag)
    if not available:
        return None
    first_choice = available.get(gender)
    if first_choice:
        return first_choice
    alternate = 'female' if gender == 'male' else 'male'
    return available.get(alternate)

if __name__ == '__main__':
    list_languages()
    list_voices()
