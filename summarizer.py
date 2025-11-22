import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from textblob import TextBlob
from importlib import resources

from symspellpy import SymSpell, Verbosity
import re

# Download NLTK resources once
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)


sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Load dictionary (using built-in dictionary from symspellpy package)
dictionary_path = str(resources.files("symspellpy").joinpath("frequency_dictionary_en_82_765.txt"))
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)


def chunk_text(text, chunk_size=1500):
    """Split large text into smaller chunks of approximately chunk_size characters."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

skip_terms = ["TCP/IP", "VLAN", "SDN", "BGP", "MPLS", "QoS", "IDS/IPS", "VPN", "HTTP", "HTTPS", "FTP", "SSH", "API", "URL"]


def is_safe_word(word):
    """
    Checks if a word is safe to correct.
    Skips: ALL CAPS words, numbers, special chars, and skip terms.
    Allows: Properly capitalized words (Title Case).
    """
    # Skip if word is in skip terms
    if word in skip_terms or word.upper() in skip_terms:
        return False
    
    # Skip if word is ALL CAPS (likely an acronym)
    if word.isupper() and len(word) > 1:
        return False
    
    # Skip if word contains numbers or special characters
    if re.search(r"[0-9/:@]", word):
        return False
    
    return True


def remove_repeated_chars(word):
    """
    Reduces repeated characters (more than 2) to 2 occurrences.
    Example: 'Helllo' -> 'Hello', 'tesst' -> 'tesst'
    """
    return re.sub(r'(.)\1{2,}', r'\1\1', word)


def correct_text_skip_links(text):
    """
    Fast + safe spell correction using SymSpell.
    - Skips URLs, acronyms, tech terms, numbers.
    - Fixes repeated characters.
    - Preserves capitalization & punctuation.
    - Preserves spacing so sentence tokenization works.
    """
    if not text or not isinstance(text, str):
        return text

    url_pattern = r'(https?://\S+|www\.\S+)'
    parts = re.split(f'({url_pattern})', text)

    out = []

    for part in parts:

        # If URL → keep original
        if re.match(url_pattern, part):
            out.append(part)
            continue

        # Tokenize words + punctuation
        tokens = re.findall(r'\w+|\S', part)

        corrected = []

        for token in tokens:

            # Skip punctuation, symbols, brackets
            if not token.isalpha():
                corrected.append(token)
                continue

            # Skip unsafe words (acronyms, tech terms, numbers, etc.)
            if not is_safe_word(token):
                corrected.append(token)
                continue

            # Reduce repeated characters
            cleaned = remove_repeated_chars(token)

            # Skip super short tokens
            if len(cleaned) < 2:
                corrected.append(token)
                continue

            lookup_word = cleaned.lower()

            suggestions = sym_spell.lookup(
                lookup_word,
                Verbosity.CLOSEST,
                max_edit_distance=2
            )

            if suggestions:
                best = suggestions[0].term

                # Restore capitalization style
                if token.istitle():
                    best = best.capitalize()
                elif token.isupper():
                    best = best.upper()

                corrected.append(best)
            else:
                corrected.append(token)

        # ------------------------------
        # FIXED: Proper spacing rebuild
        # ------------------------------
        rebuilt = []
        for i, t in enumerate(corrected):
            if i == 0:
                rebuilt.append(t)
                continue

            prev = rebuilt[-1]

            # No space before punctuation
            if re.match(r'[\.,!?;:]', t):
                rebuilt.append(t)
            # Add space after punctuation for next word
            elif re.match(r'.*[\.,!?;:]$', prev):
                rebuilt.append(" " + t)
            # Word after word → space
            elif prev[-1].isalnum() and t[0].isalnum():
                rebuilt.append(" " + t)
            else:
                rebuilt.append(t)

        out.append("".join(rebuilt))

    return "".join(out)

def summarize_text(text, num_sentences=5, correct_words=False):
    """
    Extractive summarization.
    Returns a dictionary with both HTML and text formats.
    """
    if correct_words:
        corrected = correct_text_skip_links(text)
        # Avoid using empty corrected text
        if corrected and corrected.strip():
            text = corrected

    # Tokenize sentences
    sentences = sent_tokenize(text)

    if len(sentences) <= num_sentences:
        # HTML format
        list_items = "".join([f"<li>{s}</li>" for s in sentences])
        html_summary = f"<ol>{list_items}</ol>"
        # Text format
        text_summary = "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
        return {"html": html_summary, "text": text_summary}

    stop_words = set(stopwords.words("english"))
    words = [
        w.lower() for w in word_tokenize(text)
        if w.isalnum() and w.lower() not in stop_words
    ]

    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1

    sentence_scores = {}
    for sent in sentences:
        score = sum(word_freq.get(w.lower(), 0) for w in word_tokenize(sent))
        sentence_scores[sent] = score

    # Select top sentences
    top_sentences = sorted(
        sentence_scores,
        key=sentence_scores.get,
        reverse=True
    )[:num_sentences]

    # Preserve original order
    top_set = set(top_sentences)
    ordered_summary = [s for s in sentences if s in top_set]

    # HTML format
    list_items = "".join([f"<li>{s}</li>" for s in ordered_summary])
    html_summary = f"<ol>{list_items}</ol>"

    # Text format
    text_summary = "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(ordered_summary)])
    return {"html": html_summary, "text": text_summary}




# def is_safe_word(word):
#     """
#     Checks if a word is safe to correct.
#     Skips: ALL CAPS words, numbers, special chars, and skip terms.
#     Allows: Properly capitalized words (Title Case).
#     """
#     # Skip if word is in skip terms
#     if word in skip_terms or word.upper() in skip_terms:
#         return False
    
#     # Skip if word is ALL CAPS (likely an acronym)
#     if word.isupper() and len(word) > 1:
#         return False
    
#     # Skip if word contains numbers or special characters
#     if re.search(r"[0-9/:@]", word):
#         return False
    
#     return True




# def correct_text_skip_links(text):
#     """
#     Corrects text using TextBlob but skips URLs and technical terms.
#     Also handles repeated character typos.
#     """
#     url_pattern = r'(https?://\S+|www\.\S+)'
#     parts = re.split(f'({url_pattern})', text)

#     corrected_parts = []
#     for part in parts:
#         if re.match(url_pattern, part):
#             corrected_parts.append(part)
#         else:
#             # Correct only safe words
#             corrected_words = []
#             for w in part.split():
#                 if is_safe_word(w):
#                     try:
#                         # First remove repeated characters
#                         w_cleaned = remove_repeated_chars(w)
#                         # Then apply TextBlob correction
#                         corrected = str(TextBlob(w_cleaned).correct())
#                         corrected_words.append(corrected)
#                     except:
#                         corrected_words.append(w)
#                 else:
#                     corrected_words.append(w)
#             corrected_parts.append(" ".join(corrected_words))

#     return "".join(corrected_parts) 
