# Response Handler
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from llm_handler import LlmHandler
from settings import *
from cache_handler import LRUCache, LFUCache
import hashlib
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import simpledialog
from dotenv import load_dotenv
import base64

load_dotenv()

class ResponseHandler:
    """
    Handles response caching and retrieval for the chatbot.
    Uses LRU (Least Recently Used) and LFU (Least Frequently Used) caching strategies
    to optimize response storage and reuse.
    """
    def __init__(self, core):
        self.core = core
        self.sim = False
        self.lru_cache = LRUCache(MAX_LRU_SIZE)
        self.lfu_cache = LFUCache(MAX_LFU_SIZE)
        self.score_file = "score.txt"
        self.score = 0
        self.pos_points = 0
        self.neg_points = 0
        self.level = STARTING_LEVEL
        self.uncensored = False
        self.api_key = os.getenv("API_KEY")
        self.url = 'https://www.virustotal.com/api/v3/urls/'

        self.on_init()

    def on_init(self):
        """Initializes the necessary components for the class instance."""
        self.llm = LlmHandler()
        self.cache = self.load_cache()
        self.stemmer = PorterStemmer()
        self.high_score = self.load_score()

    def get_text_input(self, prompt):
        """Creates a temporary popup to take user input and return the text."""
        root = tk.Tk()
        root.withdraw()
        user_input = simpledialog.askstring("Input", prompt)
        root.destroy()
        return user_input

    def load_score(self):
        """Loads score from score.txt, defaulting to 0 if file is missing."""
        if os.path.exists(self.score_file):
            try:
                with open(self.score_file, "r") as file:
                    return int(file.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

    def scan_url(self):
        url = self.get_text_input("URL to scan: ")
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        headers = {
            'x-apikey': self.api_key
        }
        # Use requests.get instead of request.get
        response = requests.get(f"{self.url}{url_id}", headers=headers)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            # Check the URL's analysis results for phishing
            if data['data']['attributes']['last_analysis_stats']['malicious'] > 0:
                self.core.queue("Warning: URL is malicious!")
                return data
            else:
                self.core.queue("URL is safe!")
                return data
        else:
            logging.error(f"Error: Failed to fetch URL analysis. Status code: {response.status_code}")
            return None

    def save_score(self):
        """Saves the current score to score.txt."""
        with open(self.score_file, "w") as file:
            file.write(str(self.score))

    def update_score(self, value):
        """Updates score and saves it to score.txt."""
        self.score += value
        self.save_score()

    @staticmethod
    def hash_query(query):
        """Hashes a  query using MD5 for consistent cache keys."""
        return hashlib.md5(query.encode()).hexdigest()

    def load_cache(self):
        """Loads cached responses from file, initializing LRU and LFU caches."""
        if not os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'w') as file:
                json.dump({'lru': {}, 'lfu': {}}, file)
            return

        with open(CACHE_FILE, 'r') as file:
            data = json.load(file)
            self.lru_cache.load(data.get('lru', {}))
            self.lfu_cache.load(data.get('lfu', {}))

    def save_cache(self):
        """Saves the current cache state to a file."""
        with open(CACHE_FILE, 'w') as file:
            json.dump({'lru': self.lru_cache.to_dict(), 'lfu': self.lfu_cache.to_dict()}, file)

    def extract_key_phrases(self, query):
        """Extracts key phrases from the query using stemming and removes stop words."""
        stop_words = set(stopwords.words('english'))
        words = re.sub(r'[^a-zA-Z\s]', '', query.lower()).split()
        word_counts = Counter([self.stemmer.stem(word) for word in words if word not in stop_words])
        result = list(word_counts.keys())
        if not result:
            return query.split()
        if result and result[0] in EXCLUDED_PREFIXES:
            result.pop(0)
        return result

    def fetch_and_store(self, query, query_hash, intent):
        """Fetches a fresh response from the LLM and stores it in the cache."""
        new_response = []
        for chunk in self.llm.get_response(query):
            if chunk.strip():
                new_response.append(chunk)

        new_response = ' '.join(new_response)
        self.add_response(query, query_hash, intent, new_response)

    def add_response(self, query, query_hash, intent, response):
        """Adds a response to the LFU cache under the given intent and updates the LRU cache."""
        existing_responses = self.lfu_cache.get(intent) or []

        if response not in existing_responses:
            existing_responses.append(response)
            self.lfu_cache.put(intent, existing_responses)

        self.lru_cache.put(query_hash, {'intent': intent})
        self.save_cache()

    def replace_words_with_numbers(self, text):
        pattern = re.compile(r'\b(' + '|'.join(WORD_TO_NUM.keys()) + r')\b', re.IGNORECASE)
        return pattern.sub(lambda x: WORD_TO_NUM[x.group().lower()], text)

    def dark_web_scan(self, limit=5):
        """Scans the dark web for leaked data related to given query."""
        query = self.get_text_input("Enter search term (email, username, company): ")

        response = requests.get(DARK_WEB_SEARCH_URL, params={"q": query})

        if response.status_code != 200:
            self.core.queue("Failed to fetch dark web results.")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True)][:limit]

        if not links:
            self.core.queue("No results found on the dark web.")
            return

        self.core.queue(f"\nDark Web Results for '{query}':")
        for link in links:
            self.core.cli.print_assistant_response(f"{link}")

    def handle(self, query):
        """
        Processes a user query:
        - Checks the cache for responses if at least 3 exist for the intent.
        - Uses the last response tracking to avoid immediate repetition.
        - Fetches a new response in the background while serving a cached response.
        """
        query = self.replace_words_with_numbers(query)
        query_hash = self.hash_query(query.lower())
        cached_data = self.lru_cache.get(query_hash) or self.lfu_cache.get(query_hash)
        intent_name = '.'.join(self.extract_key_phrases(query))

        if "help" in intent_name:
            self.core.cli.print_help_text()

        elif "uncensor" in intent_name and self.uncensored == False:
            self.uncensored = True
            self.core.queue(f"{NAME} has been uncensored.")
            self.llm.prompt = f"{UNCENSORED_PROMPT}"
            return

        elif "censor" in intent_name and self.uncensored == True:
            self.uncensored = False
            self.core.queue(f"{NAME} has been censored.")
            self.llm.prompt = f"{GEN_PROMPT}"
            return

        elif any(word in intent_name for word in ("dark.web", "tor", "onion")) and any(word in intent_name for word in ("scan", "lookup", "search")):
            self.dark_web_scan()
            return

        elif any(word in intent_name for word in ("scan", "check", "valid")) and any(word in intent_name for word in ("site", "websit", "url", "link")):
            self.core.cli.print_assistant_response(self.scan_url())
            return

        if not self.sim:
            if any(word in intent_name for word in ("start", "run", "simul")) and any(word in intent_name for word in ("attack", "test", "simul")):
                self.llm.prompt = f"{SIM_PROMPT} \nLEVEL: {self.level}"
                self.sim = True

            if any(word in intent_name for word in ("scenario", "scene", "attack")) and any(word in intent_name for word in ("build", "creat")):
                attack_type = self.get_text_input("Attack Type: e.g., Phishsing")
                attack_config = self.get_text_input("Attack Config: e.g., Stealth vs Aggresive")
                defense_conditions = self.get_text_input("Defense Conditions: e.g., Firewall rules")
                query = (f"{query} {attack_type} {attack_config} {defense_conditions}")

        else:
            if any(word in intent_name for word in ("set", "said", "chang")) and any(word in intent_name for word in ("level", "difficulti")):
                matches = re.findall(r'\d+', query)
                if matches:
                    new = sum(map(int, matches))
                    if self.level != new:
                        self.level = new
                        self.core.queue(f"Level set to {self.level}")
                    else:
                        self.core.queue("Already at specified level.")
                else:
                    self.core.queue("No valid level detected.")

            if any(word in intent_name for word in ("increas", "add")) and any(word in intent_name for word in ("level", "difficulti")):
                self.level += 1
                self.core.queue(f"Level has been Increased to {self.level}")
                return
            elif any(word in intent_name for word in ("decreas", "drop")) and any(word in intent_name for word in ("level", "difficulti")):
                if not self.level<=1:
                    self.level -= 1
                    self.core.queue(f"Level has been Decreased to {self.level}")
                else:
                    self.core.queue("You're already at the lowest level")
                return

            if any(word in intent_name for word in ("stop", "close")) and any(word in intent_name for word in ("attack", "test", "simul")):
                if not self.uncensored:
                    self.llm.prompt = GEN_PROMPT
                else:
                    self.llm.prompt = UNCENSORED_PROMPT
                self.sim = False

        if cached_data and not self.sim:
            detected_intent = cached_data['intent']
            cached_responses = self.lfu_cache.get(detected_intent) or []

            if len(cached_responses) >= 2:
                last_used = self.lru_cache.get('last_used_response')
                possible_responses = [res for res in cached_responses if res != last_used] if len(cached_responses) > 1 else cached_responses
                selected_response = random.choice(possible_responses)
                self.lru_cache.put('last_used_response', selected_response)

                sentences = re.split(r'(?<=[.!?])\s+', selected_response)
                response = []
                for sentence in sentences:
                    self.core.queue(sentence, display=False)
                    response.append(sentence)
                response = ' '.join(response)
                self.core.cli.print_assistant_response(response)

                threading.Thread(target=self.fetch_and_store, args=(query, query_hash, detected_intent)).start()
                return

        response = []
        for chunk in self.llm.get_response(query):
            if chunk.strip():
                if self.sim:
                    if 'WIN' in chunk:
                        self.pos_points += 1
                        self.neg_points = 0
                        self.update_score(1)
                    elif 'LOSE' in chunk:
                        self.neg_points += 1
                        self.pos_points = 0
                        self.update_score(-1)
                    chunk = chunk.replace("LOSE", "")
                    chunk = chunk.replace("WIN", "")

                    if self.score > self.high_score:
                        self.high_score = self.score

                    # Increase level if WIN 2 times in a row and vice versa
                    if self.pos_points >= 2:
                        self.pos_points = 0
                        self.level += 1
                    elif self.neg_points >= 2:
                        self.neg_points = 0
                        self.level -= 1

                self.core.queue(chunk, display=False)
                response.append(chunk)

        response = ' '.join(response)
        if response == "":
            self.core.queue("I'm not sure how to answer that.")
        self.core.cli.print_assistant_response(response)

        if not self.sim:
            threading.Thread(target=self.add_response, args=(query, query_hash, intent_name, response)).start()
