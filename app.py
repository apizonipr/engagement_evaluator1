pip install streamlit pandas numpy nltk textblob wordcloud matplotlib
python -m textblob.download_corpora

import streamlit as st
import pandas as pd
import numpy as np
import re
import nltk
from collections import Counter

# -------------------------------------------------------------------------
# DEPENDENCIES (install with pip):
#   pip install streamlit pandas numpy nltk textblob wordcloud
#
# Optional: If TextBlob fails to find the default corpora, run once:
#   python -m textblob.download_corpora
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# Robust NLTK data download helper
# -------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def ensure_nltk_data():
    """Download required NLTK packages, retrying on failure."""
    required_packages = [
        'punkt',
        'stopwords',
        'wordnet',
        'omw-1.4',
        'averaged_perceptron_tagger_eng',  # modern NLTK package name
        'maxent_ne_chunker',
        'words',
    ]
    for pkg in required_packages:
        try:
            nltk.data.find(f'tokenizers/{pkg}') if pkg in ('punkt',) else None
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception as e:
                st.warning(f"Could not download NLTK package '{pkg}': {e}")
    # Fallback: older NLTK versions may still need the legacy tagger
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        try:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            st.warning(f"Legacy tagger fallback also failed: {e}")

ensure_nltk_data()

# -------------------------------------------------------------------------
# Optional imports with graceful fallbacks
# -------------------------------------------------------------------------
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError as e:
    WORDCLOUD_AVAILABLE = False
    WordCloud = None
    st.warning(
        "WordCloud is not installed. Word-cloud functionality will be disabled. "
        "Install it with: `pip install wordcloud`"
    )

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError as e:
    TEXTBLOB_AVAILABLE = False
    TextBlob = None
    st.warning(
        "TextBlob is not installed. Sentiment analysis and noun-phrase extraction will be disabled. "
        "Install it with: `pip install textblob` and then run `python -m textblob.download_corpora`"
    )

# -------------------------------------------------------------------------
# Streamlit page configuration
# -------------------------------------------------------------------------
st.set_page_config(page_title="Text Analysis Dashboard", layout="wide")

# -------------------------------------------------------------------------
# Fixed CSS variable (was empty/malformed)
# -------------------------------------------------------------------------
custom_css = """
    <style>
        .main {
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            color: #2c3e50;
            font-family: 'Segoe UI', sans-serif;
        }
        .stTextArea textarea {
            font-size: 16px;
            border-radius: 8px;
        }
        .metric-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .highlight {
            color: #e74c3c;
            font-weight: bold;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def safe_tokenize(text):
    try:
        return nltk.word_tokenize(text)
    except Exception as e:
        st.error(f"Tokenization failed: {e}")
        return []

def safe_pos_tag(tokens):
    """
    POS-tag tokens using the modern NLTK tagger name.
    Falls back to the legacy tagger if the new package is not available.
    """
    taggers = ['averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger']
    for tagger in taggers:
        try:
            return nltk.pos_tag(tokens, tagset=None, lang='eng')
        except LookupError:
            try:
                nltk.download(tagger, quiet=True)
                return nltk.pos_tag(tokens, tagset=None, lang='eng')
            except Exception:
                continue
        except Exception as e:
            st.warning(f"POS tagging failed with {tagger}: {e}")
    # Final fallback: return tokens without tags
    return [(tok, 'UNK') for tok in tokens]

def safe_sentiment(text):
    if not TEXTBLOB_AVAILABLE or TextBlob is None:
        return None, None
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity, blob.sentiment.subjectivity
    except Exception as e:
        st.warning(f"TextBlob sentiment failed: {e}. "
                   "If it mentions missing corpora, run: `python -m textblob.download_corpora`")
        return None, None

def safe_noun_phrases(text):
    if not TEXTBLOB_AVAILABLE or TextBlob is None:
        return []
    try:
        blob = TextBlob(text)
        return list(blob.noun_phrases)
    except Exception as e:
        st.warning(f"TextBlob noun-phrase extraction failed: {e}. "
                   "Run: `python -m textblob.download_corpora`")
        return []

def extract_entities(text):
    """Extract named entities using NLTK's chunked NE parser."""
    try:
        tokens = safe_tokenize(text)
        tagged = safe_pos_tag(tokens)
        chunks = nltk.ne_chunk(tagged, binary=False)
        entities = []
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                entities.append((" ".join(c[0] for c in chunk), chunk.label()))
        return entities
    except Exception as e:
        st.warning(f"Entity extraction failed: {e}")
        return []

def make_wordcloud(text):
    if not WORDCLOUD_AVAILABLE or WordCloud is None:
        return None
    try:
        from nltk.corpus import stopwords
        stop = set(stopwords.words('english'))
        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=stop,
            colormap='viridis'
        ).generate(text)
        return wc
    except Exception as e:
        st.warning(f"WordCloud generation failed: {e}")
        return None

# -------------------------------------------------------------------------
# Main application UI
# -------------------------------------------------------------------------
st.title("📊 Text Analysis Dashboard")
st.markdown(
    "Enter text below to perform tokenization, POS tagging, sentiment analysis, "
    "named-entity extraction, and word-cloud generation."
)

user_text = st.text_area(
    "Input text",
    height=200,
    placeholder="Paste your text here..."
)

if st.button("Analyze") and user_text:
    col1, col2, col3 = st.columns(3)

    # Sentiment metrics
    polarity, subjectivity = safe_sentiment(user_text)
    with col1:
        st.metric("Polarity", f"{polarity:.2f}" if polarity is not None else "N/A")
    with col2:
        st.metric("Subjectivity", f"{subjectivity:.2f}" if subjectivity is not None else "N/A")
    with col3:
        tokens = safe_tokenize(user_text)
        st.metric("Token count", len(tokens))

    st.subheader("Tokens & POS Tags")
    if tokens:
        pos_tags = safe_pos_tag(tokens)
        pos_df = pd.DataFrame(pos_tags, columns=["Token", "POS Tag"])
        st.dataframe(pos_df, use_container_width=True)
    else:
        st.info("No tokens to display.")

    st.subheader("Named Entities")
    entities = extract_entities(user_text)
    if entities:
        ent_df = pd.DataFrame(entities, columns=["Entity", "Type"])
        st.dataframe(ent_df, use_container_width=True)
    else:
        st.info("No named entities found.")

    st.subheader("Noun Phrases")
    phrases = safe_noun_phrases(user_text)
    if phrases:
        st.write(Counter(phrases).most_common(20))
    else:
        st.info("No noun phrases extracted (TextBlob corpora may be missing).")

    st.subheader("Word Cloud")
    wc = make_wordcloud(user_text)
    if wc is not None:
        st.image(wc.to_array(), use_column_width=True)
    else:
        st.info("WordCloud is unavailable or failed. Install `wordcloud` to enable this feature.")

elif not user_text:
    st.info("👆 Enter some text and click **Analyze** to get started.")

st.markdown("---")
st.caption(
    "Dependencies: streamlit, pandas, numpy, nltk, textblob, wordcloud. "
    "NLTK data is downloaded automatically. For TextBlob corpora, run: `python -m textblob.download_corpora`"
)

streamlit run app.py
