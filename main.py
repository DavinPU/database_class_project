from pymongo import MongoClient
import streamlit as st
import re


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def get_movie(movie_title):
    regex = re.compile('^' + re.escape(movie_title) + '$', re.IGNORECASE)
    movie = db['movies'].find_one({'original_title': regex})

    return movie


def main():
    st.title("Movie Recommendation System")

    movie_title = st.text_input("Enter a movie title: ")

    if movie_title:
        recommend_movie = get_movie(movie_title)
        st.write("We found the movie: ")
        st.write(recommend_movie['original_title'] + " (" + str(recommend_movie['release_year']) + ")")
        st.write(recommend_movie)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    client = MongoClient("mongodb+srv://milleda:rav77e88n@cluster1.seq1fwn.mongodb.net/test")

    db = client.movies_db

    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
