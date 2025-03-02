# LLM Handler
from settings import *

class LlmHandler:
    """
    Handles interactions with the AI model by sending requests to a local API endpoint
    and processing streamed responses.
    """
    def __init__(self, prompt = GEN_PROMPT):
        """ Initializes the LlmHandler with model details and a session for API requests."""
        self.model = LLM_MODEL
        self.session = requests.Session()
        self.prompt = prompt

    def unload_model(self):
        """Sends a request to unload the model from memory."""
        try:
            data = {
                "model": self.model,
                "keep_alive": 0
            }
            response = self.session.post("http://localhost:11434/api/generate", json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to unload model: {e}")

    def get_response(self, query):
        """
        Sends a query to the AI model and streams the response.

        Args:
            query (str): The user input/query.
            LLM (str): The AI model to use.
        Yields:
            str: Processed chunks of the AI model's response.
        """
        try:
            data = {
                "model": self.model,
                "keep_alive": KEEP_ALIVE,
                "context": CONTEXT,
                "prompt": f"{query}",
                "system": f"{self.prompt}",
                "options": {
                    "num_keep": NUM_KEEP,
                    "temperature": TEMPERATURE,
                    "top_k": TOP_K,
                    "top_p": TOP_P,
                    "min_p": MIN_P,
                    "typical_p": TYPICAL_P,
                    "repeat_last_n": REPEAT_LAST_N,
                    "repeat_penalty": REPEAT_PENALTY,
                    "presence_penalty": PRESENCE_PENALTY,
                    "frequency_penalty": FREQUENCY_PENALTY,
                    "mirostat": MIROSTAT,
                    "mirostat_tau": MIROSTAT_TAU,
                    "mirostat_eta": MIROSTAT_ETA,
                    "penalize_newline": PENALIZE_NEWLINE,
                    "num_ctx": NUM_CTX,
                    "num_batch": NUM_BATCH,
                    "num_gpu": NUM_GPU,
                    "main_gpu": MAIN_GPU,
                    "use_mmap": USE_MMAP,
                    "use_mlock": USE_MLOCK,
                    "num_thread": NUM_THREAD
                }
            }
            response = self.session.post(
                "http://localhost:11434/api/generate",
                json=data,
                stream=True
            )

            buffer = []
            for chunk in response.iter_content(chunk_size=512):
                chunk_str = chunk.decode("utf-8")
                try:
                    chunk_json = json.loads(chunk_str)
                    buffer.append(chunk_json.get("response", ""))
                except json.JSONDecodeError:
                    continue
                if re.search(r'[.!?]$', ''.join(buffer)):
                    chunk_str = ' '.join(''.join(buffer).split())
                    buffer = []
                    yield chunk_str

        except requests.exceptions.RequestException as e:
            logging.error(f"Request to API Failed: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")
