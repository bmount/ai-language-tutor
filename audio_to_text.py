from io import BytesIO
from tempfile import mkstemp
import os
import base64
import whisper

# just running the model locally, synchronously for now.
# likely wise to offload to something like banana.dev. May need
# to modify their Whisper template to accept prompts.
# Also, larger models are noticeably better for this case, with
# especially marginal pronunciation. Likewise prompts are needed
# because the language detection may fail in cases of weak accent
# and word choice on part of learner.
model = whisper.load_model("base")

