import streamlit as st
import pandas as pd
import difflib
import requests

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation System")
st.markdown("### Discover similar movies instantly!")
st.markdown("---")


# ================= LOAD DATA (CACHED) =================
@st.cache_data
def load_data():
    movies = pd.read_csv('data/movies.csv')

    # Combine features (لو عندك keywords أو overview ممكن تضيفهم هنا)
    movies['content'] = movies['genres'].fillna('')

    # Vectorization
    vectorizer = TfidfVectorizer(stop_words='english')
    feature_vectors = vectorizer.fit_transform(movies['content'])

    # Similarity matrix
    similarity = cosine_similarity(feature_vectors)

    return movies, similarity


movies, similarity = load_data()


# ================= TMDB API =================
API_KEY = st.secrets["TMDB_API_KEY"]


def fetch_movie_details(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}"
    response = requests.get(url)

    if response.status_code != 200:
        return None, None, None

    data = response.json()

    if 'results' not in data or not data['results']:
        return None, None, None

    movie = data['results'][0]

    poster_path = movie.get('poster_path')
    rating = movie.get('vote_average')
    overview = movie.get('overview')

    poster_url = (
        f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path else None
    )

    return poster_url, rating, overview


# ================= RECOMMEND FUNCTION =================
def recommend(movie_name):
    list_of_titles = movies['title'].tolist()
    find_close_match = difflib.get_close_matches(movie_name, list_of_titles)

    if not find_close_match:
        return []

    close_match = find_close_match[0]
    index_of_movie = movies[movies.title == close_match].index[0]

    similarity_score = list(enumerate(similarity[index_of_movie]))
    sorted_movies = sorted(similarity_score, key=lambda x: x[1], reverse=True)

    recommended_movies = [
        movies.iloc[i[0]].title for i in sorted_movies[1:11]
    ]

    return recommended_movies


# ================= UI =================
movie_name = st.text_input("Enter your favorite movie:")

if st.button("Recommend"):

    if movie_name.strip() == "":
        st.warning("⚠️ Please enter a movie name.")
    else:
        with st.spinner("Finding similar movies..."):
            recommendations = recommend(movie_name)

        if not recommendations:
            st.error("❌ Movie not found.")
        else:
            st.success("Here are your recommendations 👇")

            cols = st.columns(5)

            for idx, movie in enumerate(recommendations):
                poster, rating, overview = fetch_movie_details(movie)

                with cols[idx % 5]:
                    if poster:
                        st.image(poster)

                    st.markdown(f"**{movie}**")

                    if rating is not None:
                        st.markdown(f"⭐ Rating: {rating}")

                    if overview:
                        st.caption(overview[:120] + "...")


st.markdown("---")
st.markdown("Made with ❤️ by **ALI BARAKAT**")
