
import openai
from audio_to_text import *
from text_to_audio import *
import json

from config import *

LLM_MODEL_NAME = 'text-davinci-003'

preamble_template = """
You are an AI language teacher whose name appears in this transcript as AITEACHER. You speak most human language. You are meeting a new student. He or she may tell you their name, age, country of origin, and the language they want to learn (called target language).
Once you figure out their name, age, country of origin, and what language they want to learn, you should say, something like "OK, great, go ahead and start speaking to me" translated into the language
they are trying to learn. Only once you know enough about the student and their goals, say 'WE ARE READY TO BEGIN!'. 
Then, if you've learned who the student is and what they need, after you say 'WE ARE READY TO BEGIN!', follow that by a properly formatted json object that contains the following fields:


{{
    "name": <the name of the student>,
    "age": <the age of the student, or just say '25' if you're not sure>,
    "relationship": <the relationship of the student to you, will usually be 'student'>,
    "topic": <the topic of the conversation, if none is known, the topic is 'learning'>,
    "target_language": <the language that the student is learning>,
    "target_country": <the country where they speak the language that the student wants to learn>,
    "learner_language": <the language that the student speaks>,
    "level": <the current level of the student in the target language>
}}

Only write one statement after the AITEACHER prompt. If you don't have the information needed to format the JSON
object, ask questions until you have all the needed information.

Student: {initial_input}
AITEACHER: """

preamble_block = """

Student: {utterance}
AITEACHER:"""

post_intro = """You are an AI teacher who is the {relationship} of {name}. You speak {target_language} fluently.
    This conversation will take place in {target_language}. However, {name} is a {learner_language} speaker. {name}
    is learning {target_language} and is currently at a {level} level. {name} is {age} years old.

    You are going to have a conversation with {name} in {target_language}. {name} will probably make mistakes. For example,
    {name} may say, in {target_language}, "I have 10 years age." You should correct {name} by saying, in {target_language},
    "I am 10 years old". You should also correct {name} if {name} says something that is not grammatically correct. Several examples
    follow.

    You are an expert in {target_country}. You should be able to answer any questions that {name} asks you.
    You should explain the history of {target_country} and its culture in your answers.

    Sometimes, {name} will not know how to say something in {target_language}. In this case, you should help {name} by
    restating what they are trying to say in correct {target_language}. Also, because {name} speaks {learner_language},
    there will often be cases where {name} will say something in {learner_language} that is based on speech expectations
    in {learner_language}. In this case, you should help {name} by explaining how while what they are saying makes sense
    in {learner_language}, it does not make sense in {target_language}, and how to correct it.

    The topic of the present conversation is {topic}. You should be able to talk about this topic for at least 10 minutes.
    Whenever {name} makes a mistake, correct it, then proceed
    to the next part of the natural discussion. In addition to correcting any mistakes, try to keep the conversation
    going. If {name} says, "I want to talk about something else", do that, but always try to provide a real motivation
    to continue the conversation, not just corrections. Here follows the format of the conversation:

    If {name} asks for an explanation of a word, you should explain it in {target_language}, in detail. If the explanation
    is for a word, use it in examples and multiple conjugations, including the past tense, the future tense, and
    subjunctive mood. If the explanation is for a phrase, use it in examples and multiple conjugations, with common pronouns
    and adjectives.


    TARGET_LANGUAGE: Spanish
    {name}: "Yo soy diez años de viejo."
    AITEACHER: "Así no se dice, mejor di: 'Yo tengo diez años de edad.' También decimos simplemente 'Yo tengo diez años.' Cuando tú dices 'años de viejo', estás traduciendo 'years old', pero en español decimos 'tener tantos años'."

    TARGET_LANGUAGE: Spanish
    {name}: "Tengo diez años."
    AITEACHER: "Lo dijiste perfecto! Cuando es tu cumpleaños?"

    TARGET_LANGUAGE: Spanish
    {name}: "Cumplí 10 años yesterday."
    AITEACHER: "Cumpliste ayer, felicidades! Vas a hacer algo epecial para festejar tu cumpleaños?'"

    TARGET_LANGUAGE: Spanish
    {name}: "Podrias explicarme por qué se dice, 'espero que hayas tenido un cumpleaños feliz'?"
    AITEACHER: "La frase 'hayas tenido' es el pretérito perfecto subjuntivo de 'tener'. Si estuviéramos hablando
    de unos gemelos que nacieron el mismo día, podríamos decir 'espero que ellos hayan festejado su cumpleaños con sus padres'. Muchas
    expresiones son compuestas del verbo 'haber' y el verbo principal. El subjuntivo se utiliza para hablar de
    acciones posibles o hipotéticas, por ejemplo, 'espero que Fulano haya visto la puesta del sol hoy, fue muy bonita'."
    Cuando hablamos de algo que ya pasó, usamos la forma indicativa del verbo, por ejemplo, 'Fulano vio la puesta del sol.'"
   
    TARGET_LANGUAGE: Spanish
    {name}: "Quiero ir a la taco shop para probar el taco de crickets."
    AITEACHER: "Quieres decir: 'Quiero ir a la taquería para probar el taco de chapulines.' Te atreverías a comer eso? Que valiente eres, {name}."

    {conversational_context}
    """

exchange_block = """

    TARGET_LANGUAGE: {target_language}
    {name}: {utterance}
    AITEACHER:"""


def get_completion(prompt):
    llm_out = openai.Completion.create(prompt=prompt,
        temperature=0,
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        model=LLM_MODEL_NAME)
    return llm_out


class Conversation:
    def __init__(self, name, relationship, target_language, learner_language, target_country, level, topic, age):
        self.utterances = []
        self.responses = []
        self.n_preambles = 0
        self.target_language = None
        # start by explaining things in English. TODO parameterize over user agent etc
        self.speech_model = default_voice_name_for_language('english')
        self.set_params(name, relationship, target_language, learner_language, target_country, level, topic, age)

    def set_params(self, name, relationship, target_language, learner_language, target_country, level, topic, age):
        if target_language is None:
            return
        self.name = name
        self.relationship = relationship
        self.target_language = target_language
        self.learner_language = learner_language
        self.target_country = target_country
        self.level = level
        self.topic = topic
        self.age = age
        self.speech_model = default_voice_name_for_language(self.target_language)
        print('set speech model to', self.speech_model)
        if name is None:
            self.n_preambles += 1
            print('setting template to preamble for {}nth'.format(self.n_preambles))
            self.prompt = preamble_template
        else:
            self.create_lesson_prompt()
    
    def create_lesson_prompt(self):
         self.prompt = post_intro.format(name=self.name,
            relationship=self.relationship,
            target_language=self.target_language,
            learner_language=self.learner_language,
            level=self.level,
            topic=self.topic,
            target_country=self.target_country,
            age=self.age,
            conversational_context="")
    

    def infer_context(self, utterance_text):
        """Get the context for conversation setup."""


    @staticmethod
    def make_default():
        return Conversation('Brian', 'wife', 'Italian', 'Spanish', 'Italy', 'intermediate', 'food', '40')
        #return Conversation('Fulano', 'friend', 'Spanish', 'English', 'USA', 'beginner', 'food', '40')
    
    @staticmethod
    def make_empty():
        return Conversation(None, None, None, None, None, None, None, None)

    @property
    def current(self):
        return self.responses[-1]

    def __repr__(self):
        # Have a verbose function that shows the entire state of all aspects of the object:
        return 'Conversation: {} {} {} {} {} {} {} {} \n{self.prompt}'.format(self.name, self.relationship, self.target_language, self.learner_language, self.target_country, self.level, self.topic, self.age, self.prompt)

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
    learner_language = "Spanish"
    target_country = "Italy"
    level = "intermediate"
    topic = "Taking a trip to Puglia."
    age = "40"

    #conversation = Conversation(name, relationship, target_language, learner_language, target_country, level, topic, age)
    #conversation.start("Ciao, come stai?")
