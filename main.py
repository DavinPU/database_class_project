import pymongo
import streamlit as st
import re
from streamlit import session_state
import time


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
        if rating_score == '':
            st.error("Please enter a movie rating")
        else:
            movie = get_movie(movie_title)
            if movie:
                watched_movie = db['WatchedMovies'].find_one({'userId': userId, 'movieId': movie['id']})
                if not watched_movie:
                    db['WatchedMovies'].insert_one({'userId': userId, 'movieId': movie['id'], 'rating': rating_score})
                    st.success(f"Added {movie_title} to your watched movies!")
                else:
                    st.warning("You have already watched this movie.")

            else:
                st.error(f"{movie_title} not found.")

            time.sleep(.5)
            st.experimental_rerun()

    menu_button = st.button("Main Menu", on_click=toggle_watch_movies())


def main():
    user = session_state['user']
    st.sidebar.write('Hello, ' + user['username'] + '!')
    st.sidebar.button('Go To Watched Movies', on_click=toggle_watch_movies)

    st.title("Movie Recommendation System")

    st.caption("Based on your current watch list, here are some recommended movies: ")

    # if movie_title:
    #     recommend_movie = get_movie(movie_title)
    #     st.write("We found the movie: ")
    #     st.write(recommend_movie['original_title'] + " (" + str(recommend_movie['release_year']) + ")")
    #     st.write(recommend_movie)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    client = pymongo.MongoClient("mongodb+srv://milleda:rav77e88n@cluster1.seq1fwn.mongodb.net/test")

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
