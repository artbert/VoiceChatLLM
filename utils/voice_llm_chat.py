import re
from functools import lru_cache
import time
import json
from base64 import b64decode, b64encode
import threading
import queue
import io
import numpy as np
from typing import Optional, Set, List, Dict

import ffmpeg
import torch
from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer
from scipy.io.wavfile import read, write

# Dictionary of common abbreviations and their expansions for TTS.
# This dictionary can be extended with more abbreviations, slang and languages.
# Keys are the abbreviations (case-insensitive matching will be applied).
# Values are the desired spoken form.
abbreviations = {"pl": {
    # --- Skróty ogólne i popularne ---
    "np.": "na przykład",
    "m.in.": "między innymi",
    "itd.": "i tak dalej",
    "itp.": "i tym podobne",
    "tzn.": "to znaczy",
    "tj.": "to jest",
    "wg": "według",
    "tzw.": "tak zwany",
    "ds.": "do spraw",
    "cdn.": "ciąg dalszy nastąpi",
    "cd.": "ciąg dalszy",
    "ww.": "wyżej wymieniony",
    "jw.": "jak wyżej",
    "br.": "bieżącego roku",
    "ub. r.": "ubiegłego roku",
    "p.n.e.": "przed naszą erą",
    "n.e.": "naszej ery",
    "A.D.": "roku pańskiego",
    "PS": "post scriptum",
    "vs": "versus",
    "etc.": "et cetera",
    "pt.": "pod tytułem",
    "zob.": "zobacz",
    "por.": "porównaj",
    "załącz.": "załącznik",
    "red.": "redakcja",
    "wz.": "w zastępstwie",
    "p.o.": "pełniący obowiązki",

    # --- Tytuły, stopnie, formy grzecznościowe ---
    "dr": "doktor",
    "prof.": "profesor",
    "mgr": "magister",
    "inż.": "inżynier",
    "hab.": "habilitowany",
    "lek.": "lekarz",
    "wet.": "weterynarii",
    "płk": "pułkownik",
    "gen.": "generał",
    "ks.": "ksiądz",
    "św.": "świętego",
    "bł.": "błogosławionego",
    "dyr.": "dyrektor",
    "prez.": "prezydent",
    "s.a.": "spółka akcyjna",
    "sp. z o.o.": "spółka zoo",
	"sp.": "spółka",
    "z o.o.": "zo",

    # --- Jednostki miar i wielkości ---
    "zł": "złotych",
    "gr": "groszy",
    "kg": "kilogram",
    "dag": "dekagram",
    "km": "kilometr",
    "m": "metr",
    "cm": "centymetr",
    "mm": "milimetr",
    "ml": "mililitr",
    "godz.": "godzina",
    "min.": "minuta",
    "proc.": "procent",
    "°C": "stopni Celsjusza",
    "V": "wolt",
    "km/h": "kilometrów na godzinę",
    "hPa": "hektopaskali",
    "kcal": "kilokalorii",

    # --- Nazwy własne, instytucje, organizacje ---
    "NFZ": "en ef zet",
    "NBP": "en be pe",
    "PKP": "pe ka pe",
    "PKS": "pe ka es",
    "PKO": "pe kao",
    "PZU": "pe zet u",
    "AGH": "a gie ha",
    "UW": "u wu",
    "UJ": "u jot",
    "SGH": "es gie ha",
    "PW": "pe wu",
    "MSW": "em es wu",
    "MSZ": "em es zet",
    "ONZ": "o en zet",
    "UE": "unia europejska",
    "USA": "u es a",
    "CBŚ": "ce be ś",
    "CBA": "ce be a",
    "ABW": "a be wu",
    "IPN": "i pe en",
    "KNF": "ka en ef",
    "PCK": "pe ce ka",
    "ZHP": "zet ha pe",
    "TVP": "te fau pe",
    "TVN": "te fau en",
    "CBOS": "cebos",
    "KRS": "ka er es",
    "UOKiK": "u o kik",
    "RP": "er pe",
    "PRL": "pe er el",
    "PZPR": "pe zet pe er",
    "NATO": "nato",
    "ZSRR": "zet es er er",
    "AK": "Armia Krajowa",
    "SB": "es be",
    "MO": "em o",
    "II RP": "druga rzeczpospolita",
    "III RP": "trzecia rzeczpospolita",
    "Poczta Pol.": "poczta polska",

    # --- Technika, biznes, medycyna, internet ---
    "VAT": "wat",
    "PKB": "pe ka be",
    "PKD": "pe ka de",
    "BHP": "be ha pe",
    "PPOŻ": "pe poż",
    "CEIDG": "ce i de gie",
    "ISBN": "i es be en",
    "GPS": "gie pe es",
    "AGD": "a gie de",
    "RTV": "er te fau",
    "PC": "pe cet",
    "IT": "aj ti",
    "AI": "ejaj",
    "WWW": "wu wu wu",
    "SMS": "es em es",
    "MMS": "em em es",
    "URL": "u er el",
    "HDMI": "ha de em i",
    "USB": "u es be",
    "Wi-Fi": "wi fi",
    "E-mail": "imejl",
    "CD": "si di",
    "DVD": "di wi di",
    "VIP": "wip",
    "CV": "si wi",
    "FAQ": "najczęściej zadawane pytania",
    "DIY": "di aj łaj",
    "ASAP": "jak najszybciej",
    "CEO": "si i oł",
    "HR": "ha er",
    "PR": "pi ar",
    "IQ": "aj kju",
    "EKG": "e ka gie",
    "EEG": "e e gie",
    "RTG": "er te gie",
    "USG": "u es gie",
    "DNA": "de en a",
    "RNA": "er en a",
    "AIDS": "ejds",
    "HIV": "hiw",
    "RM": "rezonans magnetyczny",
    "TK": "tomografia komputerowa",
    "NFC": "en ef ce",
    "LED": "led",
    "LCD": "el si di",
    "UFO": "ufo",
    "SOR": "sor",
    "R&D": "arendi",
    "venture capital": "wenczer kapital",
    "science fiction": "sajens fikszyn",

    # --- Mowa potoczna, slang, skróty z komunikatorów ---
    "thx": "dzięki",
    "btw": "przy okazji",
    "omg": "o mój boże",
    "lol": "lol",
    "wgl": "w ogóle",
    "cb": "ciebie",
    "sb": "sobie",
    "kc": "kocham cię",
    "jn": "jak nie",
    "w-f": "wu ef",
    "wf": "wu ef",
    "xd": "iks de",
    "wawa": "warszawa",
    "krk": "kraków",
    "wro": "wrocław",
    "priv": "prywatna wiadomość",
    "tbh": "szczerze powiedziawszy",
    "imho": "moim skromnym zdaniem",
    "nvm": "nieważne",
    "idk": "nie wiem",
    "jj": "już jestem",
    "sql": "es ku el",
    "js": "dżejes",
    "css": "ce es es",
    "html": "ha te em el",

    # --- Adresy i oznaczenia prawne (z kropką i bez) ---
    "ul.": "ulica",
    "al.": "aleja",
    "al": "aleja",
    "os.": "osiedle",
    "pl.": "plac",
    "woj.": "województwo",
    "pow.": "powiat",
    "gm.": "gmina",
    "gm": "gmina",
    "płn.": "północny",
    "płd.": "południowy",
    "wsch.": "wschodni",
    "zach.": "zachodni",
    "m.st.": "miasto stołeczne",
    "wlkp.": "Wielkopolska",
    "śl.": "Śląsk",
    "art.": "artykuł",
    "ust.": "ustęp",
    "par.": "paragraf",
    "pkt": "punkt",
    "nr": "numer",
    "r.": "rok",
    "w.": "wiek",
    "s.": "strona",
    "str.": "strona",
    "t.": "tom",

    # --- Wyliczanie ---
    "1.": "Po pierwsze.",
    "2.": "Po drugie.",
    "3.": "Po trzecie.",
    "4.": "Po czwarte.",
    "5.": "Po piąte.",
    "6.": "Po szóste.",
    "7.": "Po siódme.",
    "8.": "Po ósme.",
    "9.": "Po dziewiąte.",
    "10.": "Po dziesiąte.",
},
"en":{
    # Common General Abbreviations
    "ASAP": "as soon as possible",
    "BTW": "by the way",
    "FYI": "for your information",
    "LOL": "laugh out loud",
    "OMG": "oh my god",
    "BRB": "be right back",
    "TTYL": "talk to you later",
    "LMK": "let me know",
    "NVM": "never mind",
    "SMH": "shaking my head",
    "IMO": "in my opinion",
    "IMHO": "in my humble opinion",
    "ROFL": "rolling on the floor laughing",
    "AFAIK": "as far as I know",
    "TMI": "too much information",
    "TBH": "to be honest",
    "ICYMI": "in case you missed it",
    "THX": "thanks",
    "TY": "thank you",
    "TYSM": "thank you so much",
    "YW": "you're welcome",
    "YOLO": "you only live once",
    "QOTD": "quote of the day",
    "AFK": "away from keyboard",
    "IRL": "in real life",
    "DAE": "does anyone else",
    "JK": "just kidding",
    "IDK": "I don't know",
    "IDC": "I don't care",
    "IKR": "I know, right",
    "NGL": "not gonna lie",
    "HMU": "hit me up",
    "FWIW": "for what it's worth",
    "WYD": "what are you doing",
    "RN": "right now",
    "GTG": "got to go",
    "G2G": "got to go",
    "CU": "see you",
    "Cya": "see ya",
    "B4": "before",
    "BC": "because",
    "JIC": "just in case",
    "FOMO": "fear of missing out",
    "POV": "point of view",
    "TBA": "to be announced",
    "TBD": "to be decided",
    "DIY": "do it yourself",
    "FTFY": "fixed that for you",
    "GG": "good game",
    "NBD": "no big deal",
    "EOD": "end of day",
    "EOW": "end of week",
    "COB": "close of business",
    "ETA": "estimated time of arrival",
    "CC": "carbon copy", # or "credit card" depending on context - keep this in mind
    "BCC": "blind carbon copy",
    "FAQ": "frequently asked questions",
    "AKA": "also known as",
    "NP": "no problem",
    "N/A": "not applicable", # or "not available" - context matters
    "OOO": "out of office",
    "TIA": "thanks in advance",
    "NSFW": "not safe for work",
    "WFH": "work from home",
    "OMW": "on my way",
    "BRT": "be right there",
    "TBF": "to be frank", # or "to be fair" - context matters
    "TGIF": "thank goodness it's Friday",
    "TBT": "throwback Thursday",
    "TIL": "today I learned",
    "AMA": "ask me anything",
    "ELI5": "explain like I'm 5",
    "XOXO": "hugs and kisses",
    "HBD": "happy birthday",
    "W/E": "whatever", # Could also be "weekend" - context matters
    "WTF": "what the f", # Sensitive, consider context/policy
    "WYSIWYG": "what you see is what you get",
    "GOAT": "greatest of all time",
    "DM": "direct message",
    "PM": "private message",
    "OP": "original poster",
    "IRL": "in real life",
    "AFK": "away from keyboard",


    # Business/Professional (some overlap with general)
    "B2B": "business to business",
    "B2C": "business to consumer",
    "CSR": "corporate social responsibility",
    "DEI": "diversity, equity, and inclusion",
    "P/E": "price to earnings",
    "EBITDA": "earnings before interest, taxes, depreciation, and amortization",
    "CEO": "chief executive officer",
    "CFO": "chief financial officer",
    "COO": "chief operating officer",
    "HR": "human resources",
    "PR": "public relations",
    "KPI": "key performance indicator",
    "ROI": "return on investment",
    "UX": "user experience",
    "UI": "user interface",
    "CRM": "customer relationship management",
    "SME": "subject matter expert",
    "SMB": "small and medium business",
    "SaaS": "software as a service",
    "TOS": "terms of service",
    "SLA": "service level agreement",
    "R&D": "research and development",
    "RFP": "request for proposal",
    "RFI": "request for information",
    "PO": "purchase order",
    "MOU": "memorandum of understanding",
    "NDA": "non-disclosure agreement",
    "EOD": "end of day",
    "ETA": "estimated time of arrival",
    "WIP": "work in progress",
    "POC": "proof of concept",


    # Technology/Internet Specific (often pronounced as letters or words)
    "HTML": "H T M L",
    "CSS": "C S S",
    "HTTP": "H T T P",
    "HTTPS": "H T T P S",
    "URL": "U R L",
    "VPN": "V P N",
    "USB": "U S B",
    "Wi-Fi": "wi fi",
    "AI": "A I",
    "ML": "M L",
    "API": "A P I",
    "CPU": "C P U",
    "RAM": "R A M",
    "PDF": "P D F",
    "FAQ": "F A Q", # Or "frequently asked questions"
    "JPEG": "jay peg",
    "GIF": "gif", # or "jif" - depends on preference
    "SMS": "S M S",
    "MMS": "M M S",
    "GPS": "G P S",
    "CD": "C D",
    "DVD": "D V D",
    "Blu-ray": "blue ray",
    "NASA": "NASA", # pronounced as a word
    "NATO": "NATO", # pronounced as a word
    "FBI": "F B I",
    "CIA": "C I A",
    "UN": "U N",
    "EU": "E U",
    "CEO": "C E O",
    "CFO": "C F O",
    "COO": "C O O",
    "WWW": "world wide web",


    # Shortened words (often pronounced as full words)
    "abt": "about",
    "b/c": "because",
    "cuz": "because",
    "thru": "through",
    "nite": "night",
    "2moro": "tomorrow",
    "2nite": "tonight",
    "gr8": "great",
    "l8r": "later",
    "pls": "please",
    "plz": "please",
    "u": "you",
    "ur": "your", # or "you are"
    "r": "are",
    "msg": "message",
    "pic": "picture",
    "info": "information",
    "vid": "video",
    "yr": "year",
    "mo": "month",
    "wk": "week",
    "bday": "birthday",
    "bro": "brother",
    "sis": "sister",
    "fam": "family",
    "pfp": "profile picture",
    "srsly": "seriously",
    "kinda": "kind of",
    "sorta": "sort of",


    # Punctuation/Symbols (how they might be read)
    "&": "and",
    "@": "at",
    "$$$": "dollars", # or "money"
    "w/": "with",
    "w/o": "without",
    "Dr.": "doctor",
    "Mr.": "mister",
    "Mrs.": "missus",
    "Ms.": "miss",
    "St.": "saint", # or "street" depending on context
    "Ave.": "avenue",
    "Rd.": "road",
    "Blvd.": "boulevard",
    "P.S.": "postscript",
    "e.g.": "for example",
    "i.e.": "that is",
    "vs.": "versus",
    "etc.": "et cetera",
    "approx.": "approximately",
    "max.": "maximum",
    "min.": "minimum",
    "vol.": "volume",
    "fig.": "figure",
    "chap.": "chapter",
    "p.": "page",
    "pp.": "pages",
    "No.": "number",
    "Cpt.": "captain",
    "Lt.": "lieutenant",
    "Gen.": "general",
    "Col.": "colonel",
    "Sgt.": "sergeant",
    "A.M.": "A M", # ante meridiem
    "P.M.": "P M", # post meridiem
    "B.C.": "B C", # before Christ
    "A.D.": "A D", # anno domini
    "CEO.": "C E O", # Sometimes seen with a period
    "Ltd.": "limited",
    "Inc.": "incorporated",
    "Co.": "company",
    "Corp.": "corporation",
    "Dept.": "department",
    "Jan.": "january",
    "Feb.": "february",
    "Mar.": "march",
    "Apr.": "april",
    "Jun.": "june",
    "Jul.": "july",
    "Aug.": "august",
    "Sep.": "september",
    "Oct.": "october",
    "Nov.": "november",
    "Dec.": "december",
    "Mon.": "monday",
    "Tue.": "tuesday",
    "Wed.": "wednesday",
    "Thu.": "thursday",
    "Fri.": "friday",
    "Sat.": "saturday",
    "Sun.": "sunday",

}}

non_standard_chars = {"pl": "[^A-Za-z0-9 ,.:;?!ąćęłńóśźżĄĆĘŁŃÓŚŹŻ-–]+", "en": "[^A-Za-z0-9 ,.:;?!-–]+"}

# Custom stopping criteria using Event
class CustomStopCriteria(StoppingCriteria):
    def __init__(self,stop_event: threading.Event):
        super().__init__()
        self.stop_event = stop_event

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        return self.stop_event.is_set()

# Implementation of the Text Buffer Class
class TTSBuffer:
    """Buffers text tokens and emits logical chunks for TTS and display."""

    def __init__(
        self,
        min_tokens: int = 3,
        max_tokens: int = 50,
        conjunctions: Optional[Set[str]] = None,
        locale: str = "en",
    ):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.buffer: List[str] = []
        self.boundary_idx: Optional[int] = None
        # Conjunctions that mark logical breakpoints for flushing
        self.conjunctions = conjunctions or {
            "and", "but", "or", "nor", "for", "yet", "so"
        }
        self.abbrev_pattern = None
        self.non_standard_chars_pattern = None
        self.chosen_abbreviations = None
        self._compile_abbreviations(locale)

    def _is_string_in_keys(self,token: str) -> bool:
        """Check if the token is in the chosen abbreviations."""
        return any(token in key for key in self.chosen_abbreviations.keys())

    def add_token(self, token: str) -> Optional[tuple[str, str]]:
        """Add a token and return a chunk if a flush condition is met."""
        self.buffer.append(token)
        idx = len(self.buffer)
        stripped_token = token.strip()

        # Flush on sentence terminator if min_tokens reached.
        if idx >= self.min_tokens:
            if stripped_token.endswith(('?', '!')):
                return self._pop_buffer(idx)
            # Make sure that dot is not part of abbreviation
            elif stripped_token.endswith(('.')) and not self._is_string_in_keys(stripped_token):
                return self._pop_buffer(idx)

        # Mark potential boundary: comma or conjunction.
        low = stripped_token.rstrip(',:;').lower()
        if stripped_token.endswith(','):
            self.boundary_idx = idx
        if low in self.conjunctions:
            self.boundary_idx = idx - 1

        # Force flush if buffer exceeds max_tokens.
        if idx >= self.max_tokens:
            if self.boundary_idx is not None and self.boundary_idx > 0:
                return self._pop_buffer(self.boundary_idx)
            else:
                return self._pop_buffer(idx)

        return None

    def flush(self) -> Optional[tuple[str, str]]:
        """Flush any remaining tokens in the buffer."""
        if not self.buffer:
            return None
        return self._pop_buffer(len(self.buffer))
    
    def _compile_abbreviations(self, language: str = "en"):
        """Compile the regular expression pattern for abbreviations."""
        self.abbrev_pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(k) for k in abbreviations.get(language, abbreviations["en"]).keys()) + r')(?!\w)', re.I)
        self.chosen_abbreviations = abbreviations.get(language, abbreviations["en"])
        self.non_standard_chars_pattern = re.compile(non_standard_chars.get(language, non_standard_chars["en"]))
    
    def _replace_common_abbreviations(self, text: str) -> str:
        """Replace common abbreviations with their expanded form."""
        @lru_cache(maxsize=1024)
        def expand_abbrev_cached(abbrev: str) -> str:
            # Try all casing variants to find a match
            for variant in (abbrev, abbrev.lower(), abbrev.upper(), abbrev.capitalize()):
                if variant in self.chosen_abbreviations:
                    return self.chosen_abbreviations[variant]
            return abbrev  # If no match, return original

        return self.abbrev_pattern.sub(lambda m: expand_abbrev_cached(m.group(1)), text)

    def _replace_non_standard_chars(self, text: str) -> str:
        """Replace the non-standard characters with a space."""
        return self.non_standard_chars_pattern.sub(' ', text)

    def _pop_buffer(self, n: int) -> tuple[str, str]:
        """Remove first n tokens and join into display/tts chunks."""
        chunk_tokens = self.buffer[:n]
        self.buffer = self.buffer[n:]
        # Reset boundary marker if it was within the popped range
        if self.boundary_idx is not None and self.boundary_idx <= n:
            self.boundary_idx = None

        phrase_to_display = "".join(chunk_tokens)
        phrase_for_tts = phrase_to_display.strip()

        # This is to improve the pronunciation of the Piper generator.
        phrase_for_tts = phrase_for_tts.replace("(", " – ").replace(")", " – ")
        # Replace non-standard chars with space.
        phrase_for_tts = self._replace_non_standard_chars(phrase_for_tts)

        # Replacement of common abbreviations with their expansions
        phrase_for_tts = self._replace_common_abbreviations(phrase_for_tts)
        return (phrase_to_display, phrase_for_tts)

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.boundary_idx = None

# Implementation of the Application's Backend
class VoiceLLMChatBackend:
    """Manages LLM, TTS, and ASR interaction with background threads and queues."""
    def __init__(self, model, tokenizer, piper_voice, speech_recognizer):
        # Check if all essential components are provided
        self.initialized = model is not None and tokenizer is not None and piper_voice is not None and speech_recognizer is not None
        self.llm_model = model
        self.tokenizer = tokenizer
        self.piper_voice = piper_voice
        self.speech_recognizer = speech_recognizer

        # Threading primitives: Events and Queues
        self.stop_event = threading.Event()
        self.prompt_queue = queue.Queue()
        self.tts_queue = queue.Queue()
        self.display_queue = queue.Queue()

        # Application data and state
        self.chat_messages = []
        self.context_load = 0
        self.system_message = "You are a helpful voice assistant who responds in one or two short sentences. Respond without any formatting."
        self.should_print_logs = False
        # The maximum number of words that can be processed by TTS at once
        self.tts_max_words = 20

        # Background threads
        self.model_processing_thread = None
        self.tts_processor_thread = None

        # State flags and synchronization
        self.is_running = False
        self.is_model_working = False
        self.active_streamer = None
        self.lock = threading.Lock() # Lock for thread-safe access to shared resources

    def _print_logs(self, message):
        """Print logs if enabled."""
        if self.should_print_logs:
            print(message)

    def set_model_parameters(self, temperature=0.1, max_tokens = 256, top_k = 100, top_p = 1, locale="en"):
        """Sets llm model parameters for generation."""
        self.model_temperature = temperature
        self.model_top_k = top_k
        self.model_top_p = top_p
        self.model_max_new_tokens = max_tokens
        self.locale = locale
        # self.model_repetition_penalty = repetition_penalty
        # self.model_max_new_tokens = max_new_tokens

    def set_system_message(self, system_message):
        """Sets the system message for the chat."""
        self.system_message = system_message

    def start(self):
        """Starts backend threads and initializes a new chat."""
        if not self.initialized:
            print("Backend not initialized successfully. Cannot start.")
            return

        # Stop and restart if already running
        if self.model_processing_thread is not None and self.model_processing_thread.is_alive():
            self._print_logs("Application is already running. Stopping and restarting.")
            self.stop()
            time.sleep(0.5)

        self.start_new_chat()

        self.is_running = True
        self.stop_event.clear()

        # Clear queues before starting
        self._clear_queue(self.prompt_queue)
        self._clear_queue(self.tts_queue)
        self._clear_queue(self.display_queue)

        # Create and start background threads
        self.model_processing_thread = threading.Thread(target=self._model_worker, daemon=True)
        self.tts_processor_thread = threading.Thread(target=self._tts_processor, daemon=True)

        self.model_processing_thread.start()
        self.tts_processor_thread.start()
        self._print_logs("The application started.")

    def stop(self):
        """Signals threads to stop and waits for them."""
        if not self.is_running:
            print("Application is not running.")
            return

        self._print_logs("Stopping application...")
        self.is_running = False
        self.stop_event.set()
        self.prompt_queue.put(None) # Unblock model worker's get()

        timeout_seconds = 5

        if self.model_processing_thread is not None and self.model_processing_thread.is_alive():
            self._print_logs("Waiting for model worker to stop...")
            self.model_processing_thread.join(timeout=timeout_seconds)
            if self.model_processing_thread.is_alive():
                self._print_logs("Warning: Model worker thread did not join gracefully within timeout.")
            self.model_processing_thread = None

        if self.tts_processor_thread is not None and self.tts_processor_thread.is_alive():
            self._print_logs("Waiting for TTS processor to stop...")
            self.tts_processor_thread.join(timeout=timeout_seconds)
            if self.tts_processor_thread.is_alive():
                self._print_logs("Warning: TTS processor thread did not join gracefully within timeout.")
            self.tts_processor_thread = None

        print("The application stopped.")

    def interrupt_response(self):
        """Interrupts current model response and TTS."""
        if not self.is_model_working and self.tts_queue.empty() and self.display_queue.empty():
            self._print_logs("No active response to interrupt.")
            return

        self._print_logs("Interrupting response...")
        self.stop_event.set()

        wait_time = 0
        while self.is_model_working and wait_time < 5:
            time.sleep(0.1)
            wait_time += 0.1
        if self.is_model_working:
            self._print_logs("Warning: Model worker still appears busy after interruption signal.")

        self._print_logs("Clearing TTS and display queues...")
        self._clear_queue(self.tts_queue)
        self._clear_queue(self.display_queue)

        self.display_queue.put(None) # Signal interruption to frontend
        self._print_logs("Response interruption complete.")

    def send_prompt(self, prompt: str):
        """Adds a user prompt to the queue. Interrupts current response."""
        if not self.initialized:
            print("Backend not initialized successfully. Cannot send prompt.")
            return

        trimmed_prompt = prompt.strip()
        if prompt and isinstance(prompt, str) and trimmed_prompt:
            # Interrupt any ongoing response before adding a new prompt.
            if self.is_model_working or not self.tts_queue.empty() or not self.display_queue.empty():
                 self.interrupt_response()
                 time.sleep(0.1)

            self._print_logs(f"Sending prompt to model worker queue: '{trimmed_prompt[:50]}...'")
            self.prompt_queue.put(trimmed_prompt)
        else:
            self._print_logs("Attempted to send an empty or invalid prompt.")

    def get_completed_data_chunk(self, timeout: float = 0.1) -> Optional[tuple[str, str]]:
        """Retrieves a completed sentence and audio chunk for display."""
        try:
            item = self.display_queue.get(timeout=timeout)
            if item is None:
                self._print_logs("Received None signal from display queue.")
                return None
            return item
        except queue.Empty:
            return ("", "")
        except Exception as e:
            self._print_logs(f"Error getting data chunk from display queue: {e}")
            return None

    def get_last_response(self) -> Optional[str]:
        """Retrieves the content of the last assistant message."""
        with self.lock:
            for message in reversed(self.chat_messages):
                if message.get("role") == "assistant":
                    return message.get("content", "")
        return None

    def get_context_load(self) -> int:
        """Returns estimated tokens in chat context."""
        with self.lock:
             return self.context_load if self.initialized else 0

    def start_new_chat(self):
        """Clears chat history and resets context."""
        if not self.initialized:
            print("Backend not initialized successfully. Cannot start new chat.")
            return

        # Interrupt ongoing response before clearing chat
        if self.is_model_working or not self.tts_queue.empty() or not self.display_queue.empty():
            self._print_logs("Interrupting ongoing response before starting new chat.")
            self.interrupt_response()
            time.sleep(0.1)

        self.context_load = 0
        with self.lock:
             self.chat_messages.clear()
             self.chat_messages.append({"role": "system", "content": self.system_message})

        self._print_logs("New chat started. History cleared.")

    def _update_chat_history(self, role: str, message: str):
        """Adds a message to the chat history thread-safely."""
        if role and message is not None:
            with self.lock:
                self.chat_messages.append({"role": role, "content": message})
        else:
            self._print_logs(f"Attempted to add invalid message to history. Role: {role}, Message: {message}")

    def _clear_queue(self, q: queue.Queue):
        """Clears all items from a queue."""
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                pass
            except Exception as e:
                self._print_logs(f"Error clearing queue {q}: {e}")

    def _prepare_model_inputs(self) -> Optional[Dict[str, torch.Tensor]]:
        """Prepares model inputs from chat history."""
        if not self.initialized:
             print("Backend not initialized. Cannot prepare model inputs.")
             return None
        try:
            # Apply chat template and tokenize
            text = self.tokenizer.apply_chat_template(self.chat_messages, tokenize=False, add_generation_prompt=True)
            self._print_logs(f"Prepared prompt text: {text[:100]}...")
            model_inputs = self.tokenizer([text], return_tensors="pt")
            self._print_logs("Model inputs tokenized.")

            # Move inputs to GPU if available
            if torch.cuda.is_available():
                try:
                    model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}
                    self._print_logs("Model inputs moved to GPU.")
                except Exception as e:
                    self._print_logs(f"Warning: Could not move model inputs to GPU: {e}. Using CPU instead.")

            return model_inputs

        except Exception as e:
            self._print_logs(f"Error preparing model inputs: {e}")
            self._update_chat_history("assistant", f"Error preparing prompt: {e}")
            self._signal_response_end(interrupted=True)
            return None

    def _signal_response_end(self, interrupted: bool = False):
        """Signals end of response stream to TTS processor."""
        self.tts_queue.put({"data": None, "interrupted": interrupted})
        self._print_logs(f"Signal end of response stream to tts_queue (interrupted={interrupted}).")

    def _model_worker(self):
        """Background thread processing prompts and streaming LLM output."""
        self._print_logs("Model worker started.")

        while self.is_running:
            try:
                prompt = self.prompt_queue.get(timeout=1.0)
                if prompt is None:
                    self._print_logs("Model worker received shutdown signal.")
                    break

                self._print_logs(f"Model worker processing prompt: '{prompt[:50]}...'")
                self._update_chat_history("user", prompt)

                self.stop_event.clear()

                streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

                with self.lock:
                    self.active_streamer = streamer

                stopping_criteria = StoppingCriteriaList([CustomStopCriteria(self.stop_event)])

                model_inputs = self._prepare_model_inputs()
                if model_inputs is None:
                    self._print_logs("Model input preparation failed. Skipping prompt processing.")
                    continue

                generation_kwargs = {
                    "input_ids": model_inputs["input_ids"],
                    "attention_mask": model_inputs["attention_mask"],
                    "streamer": streamer,
                    "stopping_criteria": stopping_criteria,
                    "max_new_tokens": self.model_max_new_tokens,
                    "do_sample": True if self.model_temperature else False,
                    "temperature": self.model_temperature,
                    "top_k": self.model_top_k,
                    "top_p": self.model_top_p,
                    # "repetition_penalty": repetition_penalty
                    # "num_return_sequences": 1,
                    # "repetition_penalty": 1.1
                }

                input_ids_sizes = [len(input_ids) for input_ids in model_inputs["input_ids"]]

                model_thread = threading.Thread(target=self._generate_response, args=(input_ids_sizes, generation_kwargs))
                self.is_model_working = True
                model_thread.start()

                self._process_stream(streamer)

                model_thread.join()
                self._print_logs("Model generation thread joined.")

                with self.lock:
                    self.active_streamer = None
                self.is_model_working = False

                self._print_logs("Model worker finished processing prompt.")

            except queue.Empty:
                continue
            except Exception as e:
                self._print_logs(f"Critical error in model worker loop: {e}")
                self.is_model_working = False
                self.stop_event.set()
                self._signal_response_end(interrupted=True)
                time.sleep(1)
                continue

        self._print_logs("Model worker stopped.")

    def _generate_response(self, input_ids_sizes: List[int], generation_kwargs: Dict):
        """Generates LLM response and updates chat history."""
        self._print_logs("Starting LLM generation...")
        try:
            all_generated_ids = self.llm_model.generate(**generation_kwargs)
            self._print_logs("LLM generation finished.")

            # Calculate context load
            if all_generated_ids is not None and len(all_generated_ids) > 0 and all_generated_ids[0] is not None and len(all_generated_ids[0]) > 0:
                with self.lock:
                    self.context_load = len(all_generated_ids[0])
                self._print_logs(f"Context load updated: {self.context_load} tokens.")
            else:
                with self.lock:
                    self.context_load = sum(input_ids_sizes) if input_ids_sizes else 0
                self._print_logs(f"Context load updated (no new tokens generated): {self.context_load} tokens.")

            # Extract newly generated tokens
            generated_ids = []
            if all_generated_ids is not None and len(all_generated_ids) > 0 and input_ids_sizes and len(input_ids_sizes) > 0:
                for size, output_ids in zip(input_ids_sizes, all_generated_ids):
                    if output_ids is not None and size is not None and len(output_ids) > size:
                        generated_ids.append(output_ids[size:])
                    elif output_ids is not None and size is not None and len(output_ids) <= size:
                        self._print_logs("Warning: Output sequence length <= input sequence length. No new tokens generated?")
                    elif output_ids is None or size is None:
                        self._print_logs("Warning: Invalid output_ids or input_ids_size encountered during token extraction.")

            # Decode generated tokens
            response = ""
            if generated_ids and generated_ids[0] is not None and len(generated_ids[0]) > 0:
                response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            else:
                self._print_logs("No new tokens generated or decoding resulted in an empty string.")

            # Update chat history with full response
            if response:
                self._update_chat_history("assistant", response)
                self._print_logs("Assistant's full response added to chat history.")
            else:
                self._update_chat_history("assistant", "")
                self._print_logs("No assistant response generated to add to history.")

        except Exception as e:
            error_message = f"An error occurred during response generation: {e}"
            self._print_logs(f"Error during LLM generation in _generate_response: {e}")
            self._print_logs(error_message)
            self._update_chat_history("assistant", error_message)
            self.stop_event.set()
            self._signal_response_end(interrupted=True)

    def _process_stream(self, streamer: TextIteratorStreamer):
        """Processes streamed tokens into TTS chunks."""
        self._print_logs("Starting stream processing...")
        tts = TTSBuffer(max_tokens=self.tts_max_words, locale=self.locale)
        try:
            for token_text in streamer:
                if self.stop_event.is_set():
                    self._print_logs("Stream processing interrupted by stop event.")
                    self.tts_queue.queue.clear()
                    self.tts_queue.put({"data":None, "interrupted":True})
                    break

                if token_text == "":
                    continue

                item = tts.add_token(token_text)
                if item is not None:
                    display_sentence, tts_sentence = item
                    self._print_logs(f"Putting chunk to tts_queue: '{tts_sentence[:50]}...'")
                    self.tts_queue.put({"data":(display_sentence,tts_sentence)})

            if not self.stop_event.is_set():
                self._print_logs("Stream processing finished. Flushing remaining buffer.")
                item = tts.flush()
                if item is not None:
                    display_sentence, tts_sentence = item
                    self._print_logs(f"Putting flushed chunk to tts_queue: '{tts_sentence[:50]}...'")
                    self.tts_queue.put({"data":(display_sentence,tts_sentence)})

                self._print_logs("Signaling end of stream to tts_queue.")
                self.tts_queue.put({"data":None, "interrupted":False})

        except Exception as e:
            self._print_logs(f"Error processing stream: {e}")
            self.stop_event.set()
            self.tts_queue.queue.clear()
            self.tts_queue.put({"data":None, "interrupted":True})

    def _synthesize_audio(self, tts_sentence: str) -> Optional[str]:
        """Synthesizes audio from text and encodes as base64 WAV."""
        if not tts_sentence or not tts_sentence.strip():
            return ""

        audio_chunks_int16 = []
        try:
            self._print_logs(f"Synthesizing audio for: '{tts_sentence[:50]}...'")
            for chunk in self.piper_voice.synthesize(tts_sentence):
                if hasattr(chunk, 'audio_int16_array') and chunk.audio_int16_array is not None:
                    audio_chunks_int16.append(chunk.audio_int16_array)
                else:
                    self._print_logs(f"Warning: Received unexpected audio chunk format from Piper during synthesis.")

            if not audio_chunks_int16:
                self._print_logs(f"Warning: Piper synthesis returned no audio data for chunk: '{tts_sentence[:50]}...'")
                return ""

            concatenated_audio = np.concatenate(audio_chunks_int16)
            self._print_logs(f"Synthesized {len(concatenated_audio)} samples.")

            # Convert to WAV
            byte_io = io.BytesIO()
            write(byte_io, self.piper_voice.config.sample_rate, concatenated_audio)
            output_wav = byte_io.getvalue()

            encoded_audio = "data:audio/wav;base64,{}".format(
                str(b64encode(output_wav), "utf-8")
            )
            return encoded_audio

        except Exception as e:
            self._print_logs(f"Error during Piper synthesis or WAV encoding: {e}")
            return None

    def _tts_processor(self):
        """Background thread synthesizing audio chunks and queuing for display."""
        self._print_logs("TTS processor started.")
        while self.is_running:
            try:
                recorded_item = self.tts_queue.get(timeout=1.0)

                if recorded_item is None or recorded_item.get("data") is None:
                    self._print_logs("TTS processor received end of stream or interruption signal.")
                    self.display_queue.put(None)
                    continue

                display_sentence, tts_sentence = recorded_item["data"]
                encoded_audio = self._synthesize_audio(tts_sentence)

                if encoded_audio is not None:
                    self._print_logs(f"Putting text and audio chunk to display queue.")
                    self.display_queue.put((display_sentence, encoded_audio))
                else:
                    self._print_logs(f"TTS synthesis failed for chunk, sending text only: '{display_sentence}'")
                    self.display_queue.put((display_sentence, ""))

            except queue.Empty:
                pass
            except Exception as e:
                self._print_logs(f"Critical error in TTS processor loop: {e}")
                self.display_queue.put(None)
                time.sleep(1)
                continue

        self._print_logs("TTS processor stopped.")

    def _decode_audio(self, data: str) -> Optional[bytes]:
        """Decodes base64 audio and prepares it for VOSK using ffmpeg."""
        if data is not None and isinstance(data, str):
            try:
                binary = b64decode(data)
            except:
                return None  # Return None if decoding fails
            finally:
                process = (
                    ffmpeg.input("pipe:0")
                    .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar="16k")
                    .run_async(
                        pipe_stdin=True,
                        pipe_stdout=True,
                        pipe_stderr=True,
                        quiet=True,
                        overwrite_output=True,
                    )
                )
                output, err = process.communicate(input=binary)
                return output
        else:
            self._print_logs("Invalid or non-base64 WAV data URL provided for decoding.")
            return None

    def transcribe(self, data: str) -> str:
        """Transcribes base64 audio data using VOSK."""
        audio = self._decode_audio(data)
        transcription = ""

        if audio is not None:
            try:
                self.speech_recognizer.AcceptWaveform(audio)
                result = json.loads(self.speech_recognizer.FinalResult())
                recognized_text = result.get("text", "")
                if recognized_text:
                    transcription = recognized_text.capitalize()
                    self._print_logs(f"Transcription successful: '{transcription}'")

            except Exception as e:
                self._print_logs(f"Error during VOSK transcription: {e}")

        else:
            self._print_logs("Audio data could not be decoded for transcription.")

        return transcription