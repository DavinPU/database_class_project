import numpy as np
import random
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import pymongo

def recommend(db, session_state):
    current_user = session_state['user']['userId']
    # Get all watched movies for all users
    all_users = db['ratings'].distinct('userId')
    sample_size = 500
    sampled_users = random.sample(all_users, sample_size)

    pipeline = [{'$match': {'userId': {'$in': sampled_users}}},    {'$group': {'_id': '$userId', 'movies': {'$push': '$movieId'}}}]
    cursor = db['ratings'].aggregate(pipeline)
    all_watched_movies = {doc['_id']: doc['movies'] for doc in cursor}

    user_watched = [movie['movieId'] for movie in db['WatchedMovies'].find({'userId': current_user})]

    all_watched_movies[current_user] = [movie['movieId'] for movie in db['WatchedMovies'].find({'userId': current_user})]

    # Create a matrix of user ratings for movies

    movie_ids = sorted(db['movies'].distinct('id'))

    pipeline = [{'$match': {'userId': {'$in': list(all_watched_movies.keys())}, 'movieId': {'$in': movie_ids}}},
                {'$group': {'_id': {'userId': '$userId', 'movieId': '$movieId'}, 'rating': {'$avg': '$rating'}}},
                {'$project': {'userId': '$_id.userId', 'movieId': '$_id.movieId', 'rating': '$rating', '_id': 0}}]
    ratings = list(db['ratings'].aggregate(pipeline))
    user_ratings_matrix = np.zeros((len(all_watched_movies), len(movie_ids)))
    for i, user in enumerate(all_watched_movies.keys()):
        ratings_for_user = [rating['rating'] for rating in ratings if rating['userId'] == user]
        movie_ids_for_user = [rating['movieId'] for rating in ratings if rating['userId'] == user]
        user_ratings_matrix[i, np.searchsorted(movie_ids, movie_ids_for_user)] = ratings_for_user

    # Calculate the similarity between users
    user_similarity_matrix = cosine_similarity(user_ratings_matrix)

    # Recommend movies for a specific user

    current_user_index = list(all_watched_movies.keys()).index(current_user)
    similar_users_indices = np.argsort(user_similarity_matrix[current_user_index])[::-1][1:6]  # top 5 similar users
    not_watched_movies_indices = np.where(user_ratings_matrix[current_user_index] == 0)[
        0]  # movies not watched by the user

    similarity_sum = np.sum(user_similarity_matrix[current_user_index, similar_users_indices])

    print("CHECKPOINT 1")
    # if user has no ratings in common
    if similarity_sum == 0:
        predicted_ratings = np.zeros(len(not_watched_movies_indices))
    else:
        predicted_ratings = user_similarity_matrix[current_user_index, similar_users_indices] @ \
                            user_ratings_matrix[similar_users_indices][:, not_watched_movies_indices] / similarity_sum
    top_n_movies_indices = np.argsort(predicted_ratings)[::-1]

    # store recommend movies in a list that we can then trasnfer into a pandas dataframe
    movie_return_strings = []

    movie_ids_list = [movie_ids[not_watched_movies_indices[movie_index]] for movie_index in top_n_movies_indices]

    pipeline = [{'$match': {'id': {'$in': movie_ids_list}}},
                {'$lookup': {'from': 'WatchedMovies', 'localField': 'id', 'foreignField': 'movieId', 'as': 'watched'}},
                {'$match': {'watched.userId': {'$ne': current_user}}}, {
                    '$project': {'_id': 0, 'original_title': 1, 'release_year': 1, 'genres': 1, 'original_language': 1,
                                 'budget': 1, 'popularity': 1}}]

    # execute the aggregation pipeline and retrieve the movie data
    movie_data = list(db['movies'].aggregate(pipeline))
    for movie in movie_data:
        try:
            movie_return_strings.append([movie['original_title'], movie['release_year'],
                                         movie['genres'], movie['original_language'], movie['budget'],
                                         movie['popularity']])
        except KeyError:
            pass

    movie_dicts = [{'title': movie[0], 'release_year': movie[1], 'genres': movie[2], 'language': movie[3],
                    'budget': movie[4], 'popularity': movie[5]} for movie in movie_return_strings]

    print("CHECKPOINT 2")
    movie_df = pd.DataFrame(movie_dicts)

    # return this dataframe, and then we can easily filter out movies based on user specified preferences
    return movie_df

if __name__ == '__main__':
    client = pymongo.MongoClient("mongodb+srv://milleda:rav77e88n@cluster1.seq1fwn.mongodb.net/test")

    db = client.movies_db

    pipeline = [
        {"$group": {"_id": None, "earliest": {"$min": "$release_year"}, "latest": {"$max": "$release_year"}}}
    ]

    # Run the aggregation query and print the results
    result = list(db['movies'].aggregate(pipeline))[0]

    # Print the results
    print("Earliest release year:", result["earliest"])
    print("Latest release year:", result["latest"])
    #recommend()