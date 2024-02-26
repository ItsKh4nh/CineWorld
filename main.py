import numpy as np
import pandas as pd
from flask import Flask, render_template, request, json
import json
import bs4 as bs
import urllib.request
import pickle
from datetime import date, datetime
import requests

# load the nlp model and tfidf vectorizer from disk
filename = "preprocessing/nlp_model.pkl"
clf = pickle.load(open(filename, "rb"))
vectorizer = pickle.load(open("preprocessing/transform.pkl", "rb"))


# converting list of string to list (eg. "["abc","def"]" to ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["', "")
    my_list[-1] = my_list[-1].replace('"]', "")
    return my_list


# convert list of numbers to list (eg. "[1,2,3]" to [1,2,3])
def convert_to_list_num(my_list):
    my_list = my_list.split(",")
    my_list[0] = my_list[0].replace("[", "")
    my_list[-1] = my_list[-1].replace("]", "")
    return my_list


app = Flask(__name__)

TMDB_API_KEY = (
    "6b494c120a5b63392092caf68cfa7687"  # Replace with your actual TMDB API key
)


def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_suggestions():
    data = pd.read_csv("datasets/main_data.csv")
    return list(data["movie_title"].str.capitalize())


@app.route("/")
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template("home.html", suggestions=suggestions)


@app.route("/popular-matches", methods=["POST"])
def popular_matches():
    # getting data from AJAX request
    res = json.loads(request.get_data("data"))
    movies_list = res["movies_list"]

    movie_cards = {}
    for movie_item in movies_list:
        movie_id = movie_item["id"]
        movie_details = get_movie_details(movie_id)
        if movie_details:
            poster_path = movie_details.get("poster_path", "")
            poster = (
                f"https://image.tmdb.org/t/p/original{poster_path}"
                if poster_path
                else "/static/movie_placeholder.jpeg"
            )
            movie_cards[poster] = [
                movie_details.get("title", ""),
                movie_details.get("original_title", ""),
                movie_details.get("vote_average", ""),
                (
                    datetime.strptime(
                        movie_details.get("release_date", ""), "%Y-%m-%d"
                    ).year
                    if movie_details.get("release_date")
                    else "N/A"
                ),
                movie_id,
            ]

    return render_template("recommend.html", movie_cards=movie_cards)


@app.route("/recommend", methods=["POST"])
def recommend():
    # getting data from AJAX request
    title = request.form["title"]
    cast_ids = request.form["cast_ids"]
    cast_names = request.form["cast_names"]
    cast_chars = request.form["cast_chars"]
    cast_bdays = request.form["cast_bdays"]
    cast_bios = request.form["cast_bios"]
    cast_places = request.form["cast_places"]
    cast_profiles = request.form["cast_profiles"]
    imdb_id = request.form["imdb_id"]
    poster = request.form["poster"]
    genres = request.form["genres"]
    overview = request.form["overview"]
    vote_average = request.form["rating"]
    vote_count = request.form["vote_count"]
    rel_date = request.form["rel_date"]
    release_date = request.form["release_date"]
    runtime = request.form["runtime"]
    status = request.form["status"]
    rec_movies = request.form["rec_movies"]
    rec_posters = request.form["rec_posters"]
    rec_movies_org = request.form["rec_movies_org"]
    rec_year = request.form["rec_year"]
    rec_vote = request.form["rec_vote"]
    rec_ids = request.form["rec_ids"]

    # call the convert_to_list function for every string that needs to be converted to list
    rec_movies_org = convert_to_list(rec_movies_org)
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)

    # convert string to list (eg. "[1,2,3]" to [1,2,3])
    cast_ids = convert_to_list_num(cast_ids)
    rec_vote = convert_to_list_num(rec_vote)
    rec_year = convert_to_list_num(rec_year)
    rec_ids = convert_to_list_num(rec_ids)

    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r"\n", "\n").replace(r"\"", '"')

    for i in range(len(cast_chars)):
        cast_chars[i] = cast_chars[i].replace(r"\n", "\n").replace(r"\"", '"')

    # combining multiple lists as a dictionary which can be passed to the html file so that it can be processed easily and the order of information will be preserved
    movie_cards = {
        rec_posters[i]: [
            rec_movies[i],
            rec_movies_org[i],
            rec_vote[i],
            rec_year[i],
            rec_ids[i],
        ]
        for i in range(len(rec_posters))
    }

    casts = {
        cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]]
        for i in range(len(cast_profiles))
    }

    cast_details = {
        cast_names[i]: [
            cast_ids[i],
            cast_profiles[i],
            cast_bdays[i],
            cast_places[i],
            cast_bios[i],
        ]
        for i in range(len(cast_places))
    }

    if imdb_id != "":
        # web scraping to get user reviews from IMDB site
        sauce = urllib.request.urlopen(
            "https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt".format(imdb_id)
        ).read()
        soup = bs.BeautifulSoup(sauce, "lxml")
        soup_result = soup.find_all("div", {"class": "text show-more__control"})

        reviews_list = []  # list of reviews
        reviews_status = []  # list of comments (good or bad)
        for reviews in soup_result:
            if reviews.string:
                reviews_list.append(reviews.string)
                # passing the review to our model
                movie_review_list = np.array([reviews.string])
                movie_vector = vectorizer.transform(movie_review_list)
                pred = clf.predict(movie_vector)
                reviews_status.append("Positive" if pred else "Negative")

        # getting current date
        movie_rel_date = ""
        curr_date = ""
        if rel_date:
            today = str(date.today())
            curr_date = datetime.strptime(today, "%Y-%m-%d")
            movie_rel_date = datetime.strptime(rel_date, "%Y-%m-%d")

        # combining reviews and comments into a dictionary
        movie_reviews = {
            reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))
        }

        # passing all the data to the html file
        return render_template(
            "recommend.html",
            title=title,
            poster=poster,
            overview=overview,
            vote_average=vote_average,
            vote_count=vote_count,
            release_date=release_date,
            movie_rel_date=movie_rel_date,
            curr_date=curr_date,
            runtime=runtime,
            status=status,
            genres=genres,
            movie_cards=movie_cards,
            reviews=movie_reviews,
            casts=casts,
            cast_details=cast_details,
        )

    else:
        return render_template(
            "recommend.html",
            title=title,
            poster=poster,
            overview=overview,
            vote_average=vote_average,
            vote_count=vote_count,
            release_date=release_date,
            movie_rel_date="",
            curr_date="",
            runtime=runtime,
            status=status,
            genres=genres,
            movie_cards=movie_cards,
            reviews="",
            casts=casts,
            cast_details=cast_details,
        )


if __name__ == "__main__":
    app.run(debug=True)
