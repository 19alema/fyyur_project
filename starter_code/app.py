#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from email.policy import default
import config

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
# implementing the entire app to use MIGRATE for changes to the db
migrate = Migrate(app, db);

# TODO: connect to a local postgresql database

app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI;

# ------------------------------------------------------------------------
# MODELS
# ---------------------------------------------=-----------------------
class Artist(db.Model): # Stores all information about artists
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    city = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(200))

    genres = db.Column("genres", db.ARRAY(db.String()), nullable=True)
    image_link = db.Column(db.String(600))
    facebook_link = db.Column(db.String(200))

    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))

    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f"<Artis {self.id} name: {self.name}>"


class Venue(db.Model): # Venue model storing all information related to a particular venue
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    city = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(2000), nullable=False)

    address = db.Column(db.String(2000), nullable=False)
    phone = db.Column(db.String(200))

    image_link = db.Column(db.String(600))
    facebook_link = db.Column(db.String(200))
    
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=True)
    website = db.Column(db.String(350))
    
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(350))
    # seeking_description
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f"<Venue {self.id} name: {self.name}>"


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
      return f"<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    # instead of just date = dateutil.parser.parse(value)
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

# index page
@app.route('/')
def index():
  return render_template('pages/home.html')
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  all_venue = []
  cities_and_states= set()
  # get all venues
  all_venues = Venue.query.all()


  for venue in all_venues:
    cities_and_states.add((venue.city, venue.state))

  for location in cities_and_states:
    list_of_all_venues = [] # Stores venue in particular city and State

    for venue in all_venues:
      if(venue.state == location[1]) and (venue.city == location[0]):
           upcoming_show_count =  db.session.query(Show).join(Venue).filter(Show.start_time>datetime.now()).all();

           list_of_all_venues.append({
            "id": venue.id,"name": venue.name, "num_upcoming_shows": upcoming_show_count
           })
    all_venue.append(
      {
      "state": location[1],
      "city": location[0],
      "venues": list_of_all_venues
      }
    )



  return render_template('pages/venues.html', areas=all_venue)

# Searching for a particular venues from the database
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term') # The search word or term from the input field
  search_result_venues = Venue.query.filter(Venue.name.ilike(f'%' + search_term + '%')).all()

  venue_list = []
  for avenue in search_result_venues:

      venue_list.append({
        "id": avenue.id,
        "name": avenue.name
      })
  

  response={
    "count": len(search_result_venues),
    "data": venue_list
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

# Display a specific Venue
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  the_venue = Venue.query.get(venue_id);

  if not the_venue:
    # if no venue has been returned, the user must be directed to home
    return redirect(url_for("index"))
  
  else: # If a venue exist in the db, then it should be displayed on the venue page

    all_shows = Show.query.filter_by(venue_id=venue_id).all()
    past_shows = []

    past_show_count = 0;
    upcoming_shows = []
    upcoming_show_count = 0;
  

    for a_show in all_shows:
    
      if str(a_show.start_time) > str(datetime.now()):
        upcoming_show_count += 1;
        upcoming_shows.append(
          {
            "artist_id": a_show.artist_id,
            "artist_name": a_show.artist.name,
            "artist_image_link": a_show.artist.image_link,
            "start_time": str(a_show.start_time)
          }
        )
      else:
        past_show_count += 1;
        past_shows.append(
          {
            "artist_id": a_show.artist_id,
            "artist_name": a_show.artist.name,
            "artist_image_link": a_show.artist.image_link,
            "start_time": str(a_show.start_time)
          }
        )

    id=the_venue.id
    name = the_venue.name
    city = the_venue.city
    state = the_venue.state
    genres = the_venue.genres
    website = the_venue.website
    facebook_link = the_venue.facebook_link
    seeking_talent = the_venue.seeking_talent
    seeking_description = the_venue.seeking_description
    address = the_venue.address
    phone = the_venue.phone 
    image_link = the_venue.image_link 

    venue_data={
      "id": id,"name": name,"genres": genres,"address":address,"city": city,"state": state,"phone":phone, "website":website, "facebook_link": facebook_link, "seeking_talent": seeking_talent,"seeking_description":seeking_description,"image_link": image_link,"past_shows": past_shows,"upcoming_shows": upcoming_shows,"past_shows_count": past_show_count,"upcoming_shows_count": upcoming_show_count
    }
    return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data 
    seeking_talent = form.seeking_talent.data 
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data
    website = form.website_link.data
    facebook_link = form.facebook_link.data


 
    try:
        new_venue = Venue(
        name = name, city = city,state =state,
        address = address,phone = phone, 
        image_link =image_link, genres = genres, 
        facebook_link =facebook_link, 
        seeking_description = seeking_description, 
        website = website, 
        seeking_talent =seeking_talent
        )

        # coomit new session to database
        db.session.add(new_venue)
        db.session.commit()
        print(new_venue)
      # flash success
        flash('Venue was listed!')
    except Exception as e:
          print(e)
          db.session.rollback()
      #Displayed when an error has occured when adding new venue to the database
          flash('An error occurred')
    finally:
          db.session.close()

          return render_template('pages/home.html')


# Edit Venue

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

      form = VenueForm()
 
      the_venue = Venue.query.get(venue_id)
      # Data from database with the venue Id
      venue_name = the_venue.name
      venue_genres = the_venue.genres
      venue_address = the_venue.address
      venue_city = the_venue.city
      venue_state = the_venue.state
      venue_phone_number = the_venue.phone
      venue_web_address = the_venue.website
      venue_facebook_page = the_venue.facebook_link
      venue_image_link = the_venue.image_link
      venue_talent_seek = the_venue.seeking_talent
      venue_seeking_info = the_venue.seeking_description

  # Adding the artist data after editing to the particular venue

      venue = {
      "id": venue_id,  "name": venue_name,
      "genres": venue_genres, "address": venue_address,
      "city":  venue_city ,"state": venue_state,
      "phone": venue_phone_number,"website":venue_web_address,
      "facebook_link": venue_facebook_page, "seeking_talent": venue_talent_seek,
      "seeking_description": venue_seeking_info , "image_link":venue_image_link
    }  
      return render_template('forms/edit_venue.html', form=form, venue=venue)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    form = VenueForm(request.form)
    edit_venue = Venue.query.get(venue_id)

    edit_venue.name = form.name.data
    edit_venue.genres = form.genres.data
    edit_venue.city = form.city.data
    edit_venue.state = form.state.data
    edit_venue.address = form.address.data
    edit_venue.phone = form.phone.data
    edit_venue.facebook_link = form.facebook_link.data
    edit_venue.website = form.website_link.data
    edit_venue.image_link = form.image_link.data
    edit_venue.seeking_talent = form.seeking_talent.data
    edit_venue.seeking_description = form.seeking_description.data

    db.session.commit()
    flash('Venue ' + request.form['name'] + 'has been updated')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash('An error occured while trying to update Venue')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
  
  all_artists = Artist.query.order_by(Artist.name).all() # Artists are sorted alphabetically basing on their names
  artist_data=[]

  if not all_artists:
    return redirect(url_for('index'))
     # Redirects home if there are no artists in the database
  else:
    for artist in all_artists:
      artist_data.append({
        "id": artist.id,
        "name": artist.name
      })

    return render_template('pages/artists.html', artists=artist_data)

@app.route('/artists/search', methods=['POST'])
def search_artists(): 

  artist = []
  search_term = request.form.get('search_term')
  # filter artists by case insensitive search
  search_result = Artist.query.filter(Artist.name.ilike('%' + search_term + '%'))

  for artist in search_result:
    artist.append({
      "id": artist.id,
      "name": artist.name
    })
  response = {
    'count': len(search_result),
    'data': artist
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  the_artist = Artist.query.get(artist_id)
  artist_shows = Show.query.filter_by(artist_id=artist_id).all()
  # filter shows by upcoming and past
  artist_past_show = []; 
  artist_past_show_count = 0;
  #List all the past show for the artist
  artist_upcoming_show =[]
  artist_upcoming_show_count = 0


  for show in artist_shows:

    if str(show.start_time) > str(datetime.now()):
      artist_upcoming_show_count +=1;
    artist_upcoming_show.append({
    'venue_id': show.venue_id,
    'venue_name': show.venue.name,
    'venue_image_link': show.venue.image_link,
    'start_time': str(show.start_time)
  })
   
    if str(datetime.now()) > str(show.start_time):
      artist_past_show_count += 1;
      artist_past_show.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': str(show.start_time)
    })
# ARTIST INFOMATION

  
  
   #lists all upcoming shows
  artist_id = the_artist.id
  artist_name = the_artist.name
  artist_genres = the_artist.genres
  artist_city = the_artist.city
  artist_state = the_artist.state
  artist_phone_number = (the_artist.phone[:4] + '-' + the_artist.phone[4:8] + '-' + the_artist.phone[8:])
  artist_facebook_page = the_artist.facebook_link
  artist_image_link = the_artist.image_link

  artist_data = {
    'id': artist_id, 'name': artist_name, 'genres': artist_genres,
    'city': artist_city, 'state': artist_state,
    'phone': artist_phone_number, 'facebook_link': artist_facebook_page,
   'image_link': artist_image_link, 'past_shows': artist_past_show,
    'upcoming_shows': artist_upcoming_show,'past_shows_count': artist_past_show_count,
    'upcoming_shows_count': artist_upcoming_show_count
  }

  return render_template('pages/show_artist.html', artist=artist_data)

#  Updating of artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  the_artist = Artist.query.get(artist_id)

  #Artist data from the database
  artist_id = the_artist.id
  artist_name = the_artist.name
  artist_genres = the_artist.genres
  artist_city = the_artist.city
  artist_state = the_artist.state
  artist_phone_number = (the_artist.phone[:3] + '-' + the_artist.phone[3:6] + '-' + the_artist.phone[6:])
  artist_facebook_page = the_artist.facebook_link
  artist_image_link = the_artist.image_link
  artist_seeking_venue = the_artist.seeking_venue
  artist_seeking_description = the_artist.seeking_description

  artist_data={
    "id": artist_id,  "name": artist_name,
    "genres": artist_genres, "city": artist_city,
    "state": artist_state,  "phone": artist_phone_number,
    "facebook_link": artist_facebook_page,  "image_link": artist_image_link,
    "seeking_venue": artist_seeking_venue, "seeking_description": artist_seeking_description
  }
  print(artist_data)
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  try:
    form = ArtistForm(request.form)

    edit_artist = Artist.query.get(artist_id)
    edit_artist.name = form.name.data
    edit_artist.phone = form.phone.data
    edit_artist.state = form.state.data
    edit_artist.city = form.city.data
    edit_artist.genres = form.genres.data
    edit_artist.image_link = form.image_link.data
    edit_artist.facebook_link = form.facebook_link.data
    edit_artist.seeking_venue = form.seeking_venue.data
    edit_artist.seeking_description = form.seeking_description.data

    db.session.commit()

    flash('The Artist ' + request.form['name'] + ' has updated')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash('Update unsucessful')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

#  Create a new Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
# Artist data from the form to be submitted
        form = ArtistForm(request.form)
        name=form.name.data, 
        city=form.city.data, 
        state=form.state.data,
        phone=form.phone.data, 
        genres=form.genres.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        seeking_venue = form.seeking_venue.data ,
        seeking_description = form.seeking_description.data

        try:
          new_artist = Artist(
              name=name, city=city, 
              state=state, phone=phone, 
              genres=genres,image_link=image_link,
              facebook_link=facebook_link, seeking_venue = True if seeking_venue == 'Yes' else False,
              seeking_description =seeking_description
          )
        #Adds newly created artist to the database

          db.session.add(new_artist)
          db.session.commit()
          # on successful db insert, flash success
          flash('Artist  was created')
        except Exception as e:
          print(e)
          db.session.rollback()
          flash('Artist  not listed and created')
        finally:
          db.session.close()
      
        return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  all_shows = Show.query.all() #Gets all artists......

  show_data = [] # Stores all shows from the database
  for show in all_shows:
    show_data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time)
    })
    
  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm(request.form)
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    new_show = Show(artist_id=request.form['artist_id'],venue_id=request.form['venue_id'],start_time=request.form['start_time'])
    db.session.add(new_show) #adds newly created show to the database
    db.session.commit()
    # on successful db insert, flash success
    flash(f'Show has been successfully listed!')
  
  except:
    db.session.rollback()
    # When an error has occured
    flash(f'An error occured. Can not list the show')
  finally:
    db.session.close() #close db 
  
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
