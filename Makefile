.PHONY: python help serve


serve: proxy python tts-sa-key.json
	. set-auth.sh && ./proxy &
	. set-auth.sh && ./.venv/bin/flask --app web.py:app run --reload --port 5001

help:
	@echo Available targets are "python", "run", "proxy"

python: .venv
	python3 -m venv .venv
	. ./.venv/bin/activate && pip install -r requirements.txt
proxy:
	go build || echo "Go compiler required to build project"

tts-sa-key.json:
	bash tts-setup.sh

