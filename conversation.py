
import openai
from audio_to_text import *
from text_to_audio import *
import json

from config import *

LLM_MODEL_NAME = 'text-davinci-003'

preamble_template = """
You are an AI language teacher named Luisa, whose name appears in this transcript as Luisa. You speak many but not all human languages. You only speak """ + ', '.join(prompt_supported_languages(plain=True))+ \
""".

You are meeting a new student. He or she may tell you their name, and the language they want to learn. The language they want to learn is called the target language.

If someone says something to you not in English, tell them something to the effect of "I think you are trying to say <whatever they said> in English. You can talk to me in any language, and I'll try to help you out. Pretty soon I'll start speaking new languages."

Also figure out what national variety of the language they are interested in. If the language is spoken mainly in one place, you can just figure out the country from the language.
For example if someone wants to learn Czech, that's really mainly spoken in Czech Republic. If they want to learn Portuguese, figure out if they are more
interested in Brazilian or European Portuguese. If they want to learn an uncommon variety of a large language, try to explain to them that you can teach them one that you do speak. In the
case of Spanish, call anything in the New World "American Spanish", and anything in Europe "European Spanish".

You need to figure out the student's name, and what language they want to learn, and the language code of the target language. """ + prompt_supported_languages() \
+ """


When you know those answers, and only when you know them, we go to the next step. Until you have the answers, keep asking questions until you get them.

For now, YOU MUST ONLY SPEAK ENGLISH! You will speak the target language later.

Make sure to ask them their name if you don't know it.

Once you know the student's details, say a greeting in the target language. Then say, verbatim, 'WE ARE READY TO BEGIN!'. Only after you say 'WE ARE READY TO BEGIN!',
follow the exact phrase 'WE ARE READY TO BEGIN!' by a properly formatted json object that contains the following fields:

{{
    "name": <the name of the student>,
    "target_language": <the language that the student is learning>,
    "target_country": <the country where the target language is spoken>,
    "language_code": <the language code of the target language>
}}

Remember that you must say 'WE ARE READY TO BEGIN!' in ALL CAPS. before you say the json object. Once you have said the JSON object, say nothing else.

If you don't have the information needed to format the JSON object, ask questions until you have all the needed information. If a student asks about
a language you don't know, ask them about a language as similar as possible to what they are trying to learn. For example, if a student asks about
Galego, tell them about European Portuguese. 

Student: {initial_input}
Luisa: """

preamble_block = """

Student: {utterance}
Luisa:"""

post_intro = """You are an AI teacher.

    You speak {target_language} fluently.

    This conversation will take place in {target_language}.

    Your student, {name} will probably make mistakes. For example,
    {name} may say, in {target_language}, "I have 10 years age." You should correct {name} by saying, in {target_language},
    "I am 10 years old". You should also correct {name} if {name} says something that is not grammatically correct. Several examples
    follow.

    You are an expert in {target_country}. You should be able to answer any questions that {name} asks you.
    You should explain the history of {target_country} and its culture in your answers.

    Try to talk about what you think {name} is interested in.

    Whenever {name} makes a mistake, correct it, then proceed
    to the next part of the natural discussion.
    
    If {name} asks for an explanation of a word, you should explain it in {target_language}, in detail. If the explanation
    is for a word, use it in examples and multiple conjugations, including the past tense, the future tense, and
    subjunctive mood. If the explanation is for a phrase, use it in examples and multiple conjugations, with common pronouns
    and adjectives.


    TARGET_LANGUAGE: Spanish
    {name}: "Yo soy diez años de viejo."
    Luisa: "Así no se dice, mejor di: 'Yo tengo diez años de edad.' También decimos simplemente 'Yo tengo diez años.' Cuando tú dices 'años de viejo', estás traduciendo 'years old', pero en español decimos 'tener tantos años'."

    TARGET_LANGUAGE: Spanish
    {name}: "Tengo diez años."
    Luisa: "Lo dijiste perfecto! Cuando es tu cumpleaños?"

    TARGET_LANGUAGE: Spanish
    {name}: "Cumplí 10 años yesterday."
    Luisa: "Cumpliste ayer, felicidades! Vas a hacer algo epecial para festejar tu cumpleaños?'"

    TARGET_LANGUAGE: Spanish
    {name}: "Podrias explicarme por qué se dice, 'espero que hayas tenido un cumpleaños feliz'?"
    Luisa: "La frase 'hayas tenido' es el pretérito perfecto subjuntivo de 'tener'. Si estuviéramos hablando
    de unos gemelos que nacieron el mismo día, podríamos decir 'espero que ellos hayan festejado su cumpleaños con sus padres'. Muchas
    expresiones son compuestas del verbo 'haber' y el verbo principal. El subjuntivo se utiliza para hablar de
    acciones posibles o hipotéticas, por ejemplo, 'espero que Fulano haya visto la puesta del sol hoy, fue muy bonita'."
    Cuando hablamos de algo que ya pasó, usamos la forma indicativa del verbo, por ejemplo, 'Fulano vio la puesta del sol.'"
   
    TARGET_LANGUAGE: Spanish
    {name}: "Quiero ir a la taco shop para probar el taco de crickets."
    Luisa: "Quieres decir: 'Quiero ir a la taquería para probar el taco de chapulines.' Te atreverías a comer eso? Que valiente eres, {name}."

    {conversational_context}
    """

exchange_block = """

    TARGET_LANGUAGE: {target_language}
    {name}: {utterance}
    Luisa:"""


def get_completion(prompt):
    llm_out = openai.Completion.create(prompt=prompt,
        temperature=0.6,
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        model=LLM_MODEL_NAME)
    return llm_out


class Conversation:
    def __init__(self, name, target_language, target_country):
        self.utterances = []
        self.responses = []
        self.n_preambles = 0
        self.prompt = ""
        self.target_language = None
        # start by explaining things in English. TODO parameterize over user agent etc
        self.speech_model = default_voice_name_for_language('english')
        self.set_params(name=None, target_language=None, target_country=None)

    def set_params(self, name=None, target_language=None, target_country=None, language_code=None):
        self.name = name
        self.target_language = target_language
        self.target_country = target_country
        if self.target_language:
            self.speech_model = find_best_voice(language_code)
        else:
            self.speech_model = default_voice_name_for_language('english')
        print('set speech model to', self.speech_model)
        if name is None:
            self.n_preambles += 1
            print('setting template to preamble for {}nth'.format(self.n_preambles))
            self.prompt = preamble_template.format(initial_input="")
        else:
            self.create_lesson_prompt()
    
    def create_lesson_prompt(self):
         self.prompt = post_intro.format(name=self.name,
            target_language=self.target_language,
            target_country=self.target_country,
            conversational_context="")
    

    def infer_context(self, utterance_text):
        """Get the context for conversation setup."""


    @staticmethod
    def make_default():
        return Conversation('Brian', 'Italian', 'Italy')
        #return Conversation('Fulano', 'Spanish', 'Mexico')
    
    @staticmethod
    def make_empty():
        return Conversation(None, None, None)

    @property
    def current(self):
        return self.responses[-1]

    def __repr__(self):
        # Have a verbose function that shows the entire state of all aspects of the object:
        return self.prompt

    def say(self, utterance, plain = False):
        self.utterances.append(utterance)
        if not plain and self.target_language:
            self.prompt += exchange_block.format(name=self.name, target_language=self.target_language, utterance=utterance)
        else:
            self.prompt += preamble_block.format(utterance=utterance)
        llm_out = get_completion(self.prompt)
        self.responses.append(llm_out)
        text_out = llm_out['choices'][0]['text']
        print('working w conversation status', self.prompt, '\n\n', text_out)

        # still working on setup:
        if self.target_language is None:
            if 'WE ARE READY TO BEGIN!' in text_out:
                llm_raw = text_out.split('WE ARE READY TO BEGIN!')
                llm_json = llm_raw[1]
                text_out = llm_raw[0]
                llm_json = json.loads(llm_json)
                print('WORKING WITH LLM JSON', llm_json)
                self.set_params(**llm_json)
                tmp_wav = text_to_wav(self.speech_model, text_out)
                return text_out, tmp_wav
        # TODO paramerize language / lookup
        tmp_wav = text_to_wav(self.speech_model, text_out)
        self.prompt += text_out
        print('full sy call', self.prompt)
        return llm_out['choices'][0]['text'], tmp_wav

    def start(self, utterance):
        print('trying to format', utterance, 'into', preamble_template)
        self.prompt = preamble_template.format(initial_input=utterance)
        return self.say(utterance, plain = True)

    def proceed(self, statement):
        self.prompt += statement
        llm_out = get_completion(self.prompt)
        self.history.append(llm_out)
        return llm_out


if __name__ == '__main__':
    name = "Brian"
    relationship = "wife"
    target_language = "Italian"
    target_country = "Italy"
    level = "intermediate"
    age = "40"

    #conversation = Conversation(name, relationship, target_language, target_country, level, age)
    #conversation.start("Ciao, come stai?")
