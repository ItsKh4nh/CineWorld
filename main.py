import numpy as np
import pandas as pd
from flask import Flask, render_template, request, json
import json
import bs4 as bs
import urllib.request
import pickle
from datetime import date, datetime
import requests

# Load mô hình NLP và TF-IDF vectorizer
clf = pickle.load(open("preprocessing/nlp_model.pkl", "rb"))
vectorizer = pickle.load(open("preprocessing/transform.pkl", "rb"))


# Chuyển đổi danh sách dạng chuỗi (ví dụ: "["abc","def"]" thành ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["', "")
    my_list[-1] = my_list[-1].replace('"]', "")
    return my_list


# Chuyển đổi danh sách dạng số (ví dụ "[1,2,3]" thành [1,2,3])
def convert_to_list_num(my_list):
    my_list = my_list.split(",")
    my_list[0] = my_list[0].replace("[", "")
    my_list[-1] = my_list[-1].replace("]", "")
    return my_list


app = Flask(__name__)

myAPI = "6b494c120a5b63392092caf68cfa7687"  # TMDB API key


def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={myAPI}"
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
    return render_template("home.html", suggestions=suggestions, sort_order="desc")


@app.route("/data_collect", methods=["POST"])
def data_collect():
    # Thu thập dữ liệu từ yêu cầu AJAX
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
    # Thu thập dữ liệu từ yêu cầu AJAX
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

    # Gọi hàm convert_to_list và convert_to_list_num cho những dữ liệu dạng cần chuyển đổi thành list
    rec_movies_org = convert_to_list(rec_movies_org)
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)
    cast_ids = convert_to_list_num(cast_ids)
    rec_vote = convert_to_list_num(rec_vote)
    rec_year = convert_to_list_num(rec_year)
    rec_ids = convert_to_list_num(rec_ids)

    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r"\n", "\n").replace(r"\"", '"')

    for i in range(len(cast_chars)):
        cast_chars[i] = cast_chars[i].replace(r"\n", "\n").replace(r"\"", '"')

    # Kết hợp thành một từ điển, sau đó có thể được truyền vào tệp HTML để xử lý dễ dàng hơn
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
        # Sử dụng web scraping để crawl về những dữ liệu về bình luận của người xem từ IMDB
        sauce = urllib.request.urlopen(
            "https://www.imdb.com/title/{}/reviews?ref_=tt_urv".format(imdb_id)
        ).read()
        soup = bs.BeautifulSoup(sauce, "html.parser")
        soup_result = soup.find_all("div", {"class": "text show-more__control"})

        reviews_list = []  # Danh sách các review
        reviews_status = []  # Trạng thái của các review
        for reviews in soup_result[:10]:
            reviews_text = reviews.get_text(strip=True)
            if reviews_text:
                reviews_list.append(reviews_text)
                # Sử dụng mô hình học máy để phân tích
                movie_review_list = np.array([reviews_text])
                movie_vector = vectorizer.transform(movie_review_list)
                pred = clf.predict(movie_vector)
                reviews_status.append(
                    "Positive" if pred[0] == "positive" else "Negative"
                )
        positive_count = reviews_status.count("Positive")
        total_reviews = len(reviews_status)
        positive_ratio = positive_count / total_reviews * 100

        if positive_ratio <= 20:
            sentiment = "Very Negative"
        elif 20 < positive_ratio <= 40:
            sentiment = "Mostly Negative"
        elif 40 < positive_ratio <= 60:
            sentiment = "Mixed"
        elif 60 < positive_ratio <= 80:
            sentiment = "Mostly Positive"
        else:
            sentiment = "Very Positive"

        movie_rel_date = ""
        curr_date = ""
        if rel_date:
            today = str(date.today())
            curr_date = datetime.strptime(today, "%Y-%m-%d")
            movie_rel_date = datetime.strptime(rel_date, "%Y-%m-%d")

        movie_reviews = {
            reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))
        }

        # Truyền tất cả các dữ liệu vào file HTML
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
            sentiment=sentiment,
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
            sentiment="",
            casts=casts,
            cast_details=cast_details,
        )


if __name__ == "__main__":
    app.run(debug=True)
