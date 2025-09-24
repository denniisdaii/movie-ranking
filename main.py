from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
from dotenv import load_dotenv
import os
import requests

load_dotenv()
url_search = "https://api.themoviedb.org/3/search/movie?"
url_id = "https://api.themoviedb.org/3/movie/"
base_img_url = "https://image.tmdb.org/t/p/w500"
header = {
    'accept': "application/json",
    'Authorization':f'Bearer {os.getenv('ACCESS_TOKEN')}'
}
params = {
    'query':''
}
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie_ranking.db"
# CREATE DB
db = SQLAlchemy(app)
class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class EditForm(FlaskForm):
    rating = FloatField('Your rating out of 10', validators=[NumberRange(min=0, max=10, message='Enter a valid number!')])#
    review = StringField('Your review', validators=[DataRequired('Enter a value!')])
    submit = SubmitField('Submit')
    
class AddMovieForm(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired('Enter a value')])
    submit = SubmitField('Add Movie')
# CREATE TABLE
# with app.app_context():
#     db.create_all()


# Movie 1 to Add
# new_movie = Movie(  
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# Movie 2 to Add
# movie_to_add = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )

def add_movie(new_movie:Movie):
    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
        
# add_movie(movie_to_add)        
# add_movie(new_movie)
        
@app.route("/", methods=['GET', 'POST'])
def home():
    
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    with app.app_context():
        for i in range(len(result)):
            result[i].ranking = i+1
        
    return render_template("index.html", all_movies=result)


@app.route("/edit?id=<int:id>", methods=['GET','POST'])
def edit_form(id):
    form = EditForm()
    movie_to_update = db.get_or_404(Movie, id)
    if form.validate_on_submit():
        with app.app_context():
            movie_to_update = db.get_or_404(Movie, id)
            movie_to_update.rating = form['rating'].data
            movie_to_update.review = form["review"].data
            db.session.commit()
        return redirect("/")
    movie_title = movie_to_update.title
    return render_template('edit.html', form=form, title=movie_title) 

@app.route('/delete?id=<int:id>')
def delete(id):
    book_to_delete = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect("/")    

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        params['query'] = form['movie_title'].data
        response = requests.get(url=url_search, params=params, headers=header)
        response.raise_for_status()
        movie_data = response.json()['results']
        return render_template('select.html', data=movie_data)
        
    return render_template('add.html', form=form)

@app.route('/select/<int:id>')
def select(id):
    params_id = {
        "api_key":os.getenv("API_KEY")
    }
    response = requests.get(url=f"{url_id}{id}", params=params_id, headers=header).json()
    movie_to_add = Movie(
    title=response['title'],
    year=response['release_date'],
    description=response['overview'],
    rating=0,
    ranking=0,
    review=" ",
    img_url=f"{base_img_url}{response['poster_path']}"
)
    add_movie(movie_to_add)
    movie = db.session.execute(db.select(Movie).where(Movie.title== response['title'])).scalar()

    return redirect(f'/edit%3Fid={movie.id}')
    

if __name__ == '__main__':
    app.run(debug=True)
