import os
import pickle

import streamlit as st
import pandas as pd
import requests
import gdown

# ─── 1. Get your Drive file IDs ────────────────────────────────────────────────
# Option A: from environment variables (recommended for both local & Cloud)
MOVIE_DICT_ID  = os.getenv("MOVIE_DICT_ID",  "YOUR_MOVIE_DICT_FILE_ID_HERE")
SIMILARITY_ID  = os.getenv("SIMILARITY_ID",  "YOUR_SIMILARITY_FILE_ID_HERE")

# Option B: hard-code them directly (replace the strings below)
# MOVIE_DICT_ID = "YOUR_MOVIE_DICT_FILE_ID_HERE"
# SIMILARITY_ID = "YOUR_SIMILARITY_FILE_ID_HERE"

# ─── 2. Define where to save them locally ─────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MOVIE_PKL  = os.path.join(BASE_DIR, "movie_dict.pkl")
SIM_PKL    = os.path.join(BASE_DIR, "similarity.pkl")

def download_if_needed(file_id: str, local_path: str, min_size: int = 100_000):
    """
    Download from Google Drive if missing or file is suspiciously small.
    """
    if not os.path.exists(local_path) or os.path.getsize(local_path) < min_size:
        st.info(f"⏬ Downloading `{os.path.basename(local_path)}`…")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, local_path, quiet=False)

# ─── 3. Fetch the real pickle blobs ─────────────────────────────────────────────
download_if_needed(MOVIE_DICT_ID, MOVIE_PKL)
download_if_needed(SIMILARITY_ID, SIM_PKL)

# ─── 4. Load them safely ───────────────────────────────────────────────────────
try:
    with open(MOVIE_PKL, "rb") as f:
        movies_dict = pickle.load(f)
    with open(SIM_PKL, "rb") as f:
        similarity = pickle.load(f)
except Exception as e:
    st.error(f"❌ Error loading pickles: {e}")
    st.stop()

movies = pd.DataFrame(movies_dict)

# ─── 5. Your existing Streamlit code ──────────────────────────────────────────
def fetch_postre(movie_id):
    resp = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}"
        "?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    )
    data = resp.json()
    poster = data.get("poster_path")
    if poster:
        return f"https://image.tmdb.org/t/p/w500/{poster}"
    st.warning(f"No poster for ID {movie_id}")
    return "https://via.placeholder.com/500x750?text=No+Image"

def recommend(title):
    if title not in movies.title.values:
        return ["Not in database."], ["https://via.placeholder.com/150"]
    idx       = movies[movies.title == title].index[0]
    distances = similarity[idx]
    top5      = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1:6]

    names, posters = [], []
    for i, _ in top5:
        m_id = movies.iloc[i]["id"]
        names.append(movies.iloc[i]["title"])
        posters.append(fetch_postre(m_id))
    return names, posters

st.set_page_config(page_title="M-R-S", page_icon="▶️")
st.title("🎬 Movie Recommendation System")

choice = st.selectbox("Search your movie...", movies.title.values)
if st.button("Recommend"):
    names, posters = recommend(choice)
    cols = st.columns(5)
    for col, name, img in zip(cols, names, posters):
        with col:
            st.text(name)
            st.image(img)
