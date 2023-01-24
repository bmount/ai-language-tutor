
import secrets
from flask import Flask, render_template, request, session, jsonify, g

from conversation import Conversation
from audio_to_text import *
from config import AUDIO_DIR


app = Flask(__name__, template_folder="./browser")
app.secret_key = 'super secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True

conversations = {}

#transcribe_model = BananaTranscriber()
transcribe_model = WhisperTranscriber("base")

@app.before_request
def before_request():
    if not session.get('user'):
        session['user'] = secrets.token_hex(32)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/audiox', methods=['POST'])
def handle_audio_upload():
    if 'audio' in request.files:
        audio_file = request.files['audio']
        pathname = os.path.join(AUDIO_DIR, f"{secrets.token_hex(32)}.wav")
        audio_file.save(pathname)
        results = transcribe_model.transcribe(pathname)
        results['audio_path'] = pathname
        if not conversations.get(session['user']):
            userid = session['user']
            conversation = Conversation.make_empty()
            conversations[userid] = conversation
            teacher_text, teacher_audio = conversation.start(results.get('text'))
        else:
            conversation = conversations.get(session['user'])
            teacher_text, teacher_audio = conversation.say(results.get('text'))
        response_text = teacher_text
        return jsonify(dict(student=results, teacher=dict(text=response_text, audio_path=teacher_audio)))
    else:
        # figure out the context from utterance
        # Todo handle typed input
        pass
    return 'No audio file found in the request.'

if __name__ == '__main__':
    app.run()
