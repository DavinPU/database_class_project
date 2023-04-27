import pymongo
import streamlit as st
import re
from streamlit import session_state
import time
from movie_recommender import recommend
import pandas as pd



@st.cache_data
def cached_recommendation(_db, _session_state):
    return recommend(db, session_state)


def getMaxUserID():
    result = users_collection.find_one({}, sort=[('userId', pymongo.DESCENDING)])
    return result['userId']


def switch_create_account():
    if session_state['create_account'] == True:
        session_state['create_account'] = False
    else:
        session_state['create_account'] = True


def toggle_watch_movies():
    if session_state['watched_movies'] == True:
        session_state['watched_movies'] = False
    else:
        session_state['watched_movies'] = True


def create_account():
    st.title('Create An Account')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    back_button = st.button('Back', on_click=switch_create_account)

    if st.button('Create'):
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            st.error('That user already exists!')
        else:
            if username == '' or password == '':
                st.error("Username or password can't be blank!")
            else:
                newUserId = getMaxUserID() + 1
                new_user = {'userId': newUserId, 'username': username, 'password': password}
                db['Users'].insert_one(new_user)
                st.success('Account Created!')
                session_state['create_account'] = False


def login():
    st.title('Login')
    username = st.text_input('Username: ')
    password = st.text_input('Password: ', type='password')
    login_button = st.button('Login')
    create_button = st.button('Create Account', on_click = switch_create_account)

    if login_button:
        user = users_collection.find_one({'username': username, 'password': password})

        if user:
            st.success('Logged in!')
            session_state['logged_in'] = True
            session_state['user'] = user
        else:
            st.error('Invalid username or password.')


def get_movie(movie_title):
    regex = re.compile('^' + re.escape(movie_title) + '$', re.IGNORECASE)
    movie = db['movies'].find_one({'original_title': regex})

    return movie


def watched_movies():
    userId = session_state['user']['userId']
    st.title("Your watched movies")

    watched_movies = db['WatchedMovies'].find({'userId':userId})

    movies = []
    for movie in watched_movies:
        movie_data = db['movies'].find_one({'id': movie['movieId']})
        movies.append({
            'title': movie_data['original_title'] + ' (' + str(movie_data['release_year']) + ')',
            'genre': movie_data['genres'],
            'Your score': movie['rating']
        })

    if len(movies) > 0:
        st.table(movies)
    else:
        st.write('No movies watched yet.')

    st.header('Add a new movie')
    movie_title = st.text_input('Enter movie title:', value = "")
    rating_score = st.text_input('Enter your movie rating:', value="")

    if st.button('Add'):
        try:
            rating_score = int(rating_score)
        except Exception:
            pass

        if type(rating_score) != int:
            st.error("Please enter a valid movie rating (1-5)")
        else:
            movie = get_movie(movie_title)
            if movie:
                watched_movie = db['WatchedMovies'].find_one({'userId': userId, 'movieId': movie['id']})
                if not watched_movie:
                    if rating_score > 5:
                        rating_score = 5
                    if rating_score < 0:
                        rating_score = 0
                    db['WatchedMovies'].insert_one({'userId': userId, 'movieId': movie['id'], 'rating': rating_score})
                    st.success(f"Added {movie_title} to your watched movies!")
                else:
                    st.warning("You have already watched this movie.")

            else:
                st.error(f"{movie_title} not found.")

            time.sleep(.5)
            st.experimental_rerun()

    menu_button = st.button("Main Menu", on_click=toggle_watch_movies)

def update_movies():
    #print(selected_genres)
    pass


def main():
    user = session_state['user']
    genres_list = ['Animation', 'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Foreign', 'History', 'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction', 'Thriller',
              'War', 'Western']

    st.sidebar.write('Hello, ' + user['username'] + '!')
    st.sidebar.button('Go To Watched Movies', on_click=toggle_watch_movies)

    st.title("Movie Recommendation System")

    st.caption("Based on your current watch list, here are some recommended movies: ")
    recommend_df = cached_recommendation(db, session_state).drop_duplicates(subset=['title', 'release_year'])

    get_recommend_button = st.button("Update Movies", on_click=update_movies)

    start_year, end_year = st.sidebar.slider('Range of release years', 1874, 2020, (1874, 2020))
    selected_genres = st.sidebar.multiselect('Select genres', genres_list)
    selected_budget = st.sidebar.multiselect('Select budget', ['low', 'mid', 'high'])

    subset_df = recommend_df[recommend_df['release_year'] >= start_year]
    subset_df = subset_df[subset_df['release_year'] <= end_year]

    budget_ranges = [0, 10000000, 50000000, recommend_df['budget'].max()]
    budget_labels = ['low', 'mid', 'high']
    # Create a new column in the DataFrame with the budget intervals
    subset_df['budget_range'] = pd.cut(subset_df['budget'], bins=budget_ranges, labels=budget_labels,
                                           include_lowest=True)

    if selected_budget:
        subset_df = subset_df[subset_df['budget_range'].isin(selected_budget)]


    english_only = st.sidebar.checkbox('English only', value=False)
    if english_only:
        subset_df = subset_df[subset_df['language'] == 'en']

    if selected_genres:
        subset_df = subset_df[subset_df['genres'].apply(lambda x: any(genre in x for genre in selected_genres))]

    results_df = subset_df.head(10)

    st.table(results_df[['title', 'release_year', 'genres', 'language', 'budget']])


@st.cache_resource()
def init_connection():
    db_username = st.secrets["mongo"]["username"]
    db_password = st.secrets["mongo"]["password"]
    cluster_name = st.secrets["mongo"]["cluster_name"]

    client = pymongo.MongoClient(
        f"mongodb+srv://{db_username}:{db_password}@{cluster_name}.seq1fwn.mongodb.net/test?retryWrites=true&w=majority"
    )

    return client


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #client = pymongo.MongoClient("mongodb+srv://milleda:rav77e88n@cluster1.seq1fwn.mongodb.net/test")
    client = init_connection()

    db = client.movies_db
    users_collection = db['Users']

    if 'logged_in' not in session_state:
        session_state['logged_in'] = False
    if 'create_account' not in session_state:
        session_state['create_account'] = False
    if 'watched_movies' not in session_state:
        session_state['watched_movies'] = False

    if not session_state['logged_in']:
        if not session_state['create_account']:
            login()
        else:
            create_account()


    else:
        if session_state['watched_movies']:
            watched_movies()
        else:
            main()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
