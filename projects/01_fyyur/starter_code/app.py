#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import truediv
from typing import final
import dateutil.parser
from sqlalchemy.orm import query
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import Venue, Artist, Show, db
from flask_migrate import Migrate
import sys
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database : Done
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    try:
        query = Venue.query.all()
        places = Venue.query.distinct(Venue.city, Venue.state).all()
        areas = []

        for place in places:
            venuesList = []
            for venue in query:
                if venue.city == place.city and venue.state == place.state:
                    showsCount = len(
                        [show for show in venue.shows if show.start_time > datetime.now()]
                    )
                    venuesList.append({
                        'id': venue.id,
                        'name': venue.name,
                        'num_upcoming_shows': showsCount
                    })
            areas.append({
                'city': place.city,
                'state': place.state,
                'venues': venuesList
            })
        return render_template('pages/venues.html', areas=areas)
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    try:
        search_term = request.form["search_term"]
        venues = Venue.query.filter(
            Venue.name.ilike("%" + search_term + "%")).all()
        response = {
            "count": len(venues),
            "data": []
        }
        for venue in venues:
            response["data"].append({
                'id': venue.id,
                'name': venue.name,
            })
        return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    try:
        venue = Venue.query.get(venue_id)

        past_shows_query = db.session.query(Artist, Show).join(Show).join(Venue).\
            filter(
            Show.venue_id == venue_id,
            Show.artist_id == Artist.id,
            Show.start_time < datetime.now()
        ).all()
        past_shows = []
        for artist, show in past_shows_query:
            past_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            })

        upcoming_shows_query = db.session.query(Artist, Show).join(Show).join(Venue).filter(
            Show.venue_id == venue_id,
            Show.artist_id == Artist.id,
            Show.start_time > datetime.now()
        ).all()
        upcoming_shows = []
        for artist, show in upcoming_shows_query:
            upcoming_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            })

        data = {
            "id": venue.id,
            "name": venue.name,
            "city": venue.city,
            "state": venue.state,
            "address": venue.address,
            "phone": venue.phone,
            "image_link": venue.image_link,
            "facebook_link": venue.facebook_link,
            "website": venue.website,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            'past_shows': past_shows,
            'upcoming_shows': upcoming_shows,
            'past_shows_count': len(past_shows),
            'upcoming_shows_count': len(upcoming_shows)
        }
        return render_template('pages/show_venue.html', venue=data)
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        form = VenueForm(request.form)
        newVenue = Venue(
            name=form.name.data,
            genres=form.genres.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
            website=form.website.data,
        )
        db.session.add(newVenue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for("show_venue", venue_id=newVenue.id))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Sorry, An error occurred")
        return redirect(url_for("index"))
    finally:
        db.session.close()
    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        db.session.delete(Venue.query.get(venue_id))
        db.session.commit()
        flash("Venue removed")
        return redirect("/")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Sorry! An error occurred.")
    finally:
        db.session.close()

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    try:
        query = Artist.query.all()
        data = []
        for a in query:
            data.append({"id": a.id, "name": a.name})
        return render_template('pages/artists.html', artists=data)
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('Sorry! An error occurred.')
        return redirect('/')
    finally:
        db.session.close()


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    try:
        search_term = request.form["search_term"]
        artists = Artist.query.filter(
            Artist.name.ilike("%" + search_term + "%")).all()
        response = {
            "count": len(artists),
            "data": []
        }
        for artist in artists:
            response["data"].append({
                'id': artist.id,
                'name': artist.name,
            })
        return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    try:
        artist = Artist.query.get(artist_id)

        past_shows_query = db.session.query(Venue, Show).join(Show).join(Artist).\
            filter(
            Show.artist_id == artist_id,
            Show.venue_id == Venue.id,
            Show.start_time < datetime.now()
        ).all()
        past_shows = []
        for artist, show in past_shows_query:
            past_shows.append({
                'venue_id': artist.id,
                'venue_name': artist.name,
                'venue_image_link': artist.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            })

        upcoming_shows_query = db.session.query(Venue, Show).join(Show).join(Artist).\
            filter(
            Show.artist_id == artist_id,
            Show.venue_id == Venue.id,
            Show.start_time > datetime.now()
        ).all()
        upcoming_shows = []
        for artist, show in upcoming_shows_query:
            upcoming_shows.append({
                'venue_id': artist.id,
                'venue_name': artist.name,
                'venue_image_link': artist.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            })
        data = {
            "id": artist.id,
            "name": artist.name,
            "city": artist.city,
            "state": artist.state,
            "address": artist.address,
            "phone": artist.phone,
            "image_link": artist.image_link,
            "facebook_link": artist.facebook_link,
            "website": artist.website,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            'past_shows': past_shows,
            'upcoming_shows': upcoming_shows,
            'past_shows_count': len(past_shows),
            'upcoming_shows_count': len(upcoming_shows)
        }
        return render_template('pages/show_artist.html', artist=data)
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()


#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    try:
        query = Artist.query.get(artist_id)
        if query:
            artist = {
                "id": query.id,
                "name": query.name,
                "genres": query.genres,
                "city": query.city,
                "state": query.state,
                "phone": query.phone,
                "website": query.website,
                "facebook_link": query.facebook_link,
                "seeking_venue": query.seeking_venue,
                "seeking_description": query.seeking_description,
                "image_link": query.image_link
            }
            return render_template('forms/edit_artist.html', form=form, artist=artist)
        else:
            flash("Sorry, Artist not found")
            return redirect(url_for('index'))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()
        # TODO: populate form with fields from artist with ID <artist_id>


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        form = ArtistForm(request.form)
        artistEdit = Artist.query.get(artist_id)
        artistEdit.name = form.name.data
        artistEdit.genres = form.genres.data
        artistEdit.city = form.city.data
        artistEdit.state = form.state.data
        artistEdit.phone = form.phone.data
        artistEdit.website = form.website.data
        artistEdit.facebook_link = form.facebook_link.data
        artistEdit.seeking_venue = form.seeking_venue.data
        artistEdit.seeking_description = form.seeking_description.data
        artistEdit.image_link = form.image_link.data
        db.session.commit()
        flash("Artist have been edited.")
        return redirect(url_for("show_artist", artist_id=artist_id))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Sorry! An error occured.")
        return redirect(url_for("show_artist", artist_id=artist_id))
    finally:
        db.session.close()


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    try:
        form = VenueForm()
        query = Venue.query.get(venue_id)
        if query:
            venue = {
                "id": query.id,
                "name": query.name,
                "genres": query.genres,
                "city": query.city,
                "state": query.state,
                "phone": query.phone,
                "website": query.website,
                "facebook_link": query.facebook_link,
                "seeking_talent": query.seeking_talent,
                "seeking_description": query.seeking_description,
                "image_link": query.image_link
            }
            return render_template('forms/edit_venue.html', form=form, venue=venue)
        else:
            flash("Sorry, Venue not found")
            return redirect(url_for('index'))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred')
        return redirect(url_for('index'))
    finally:
        db.session.close()


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        form = VenueForm(request.form)
        venueEdit = Venue.query.get(venue_id)
        venueEdit.name = form.name.data
        venueEdit.genres = form.genres.data
        venueEdit.city = form.city.data
        venueEdit.state = form.state.data
        venueEdit.phone = form.phone.data
        venueEdit.website = form.website.data
        venueEdit.facebook_link = form.facebook_link.data
        venueEdit.seeking_talent = form.seeking_talent.data
        venueEdit.seeking_description = form.seeking_description.data
        venueEdit.image_link = form.image_link.data
        db.session.commit()
        flash("Venue has been edited.")
        return redirect(url_for("show_venue", venue_id=venue_id))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Sorry! An error occured.")
        return redirect(url_for("show_venue", venue_id=venue_id))
    finally:
        db.session.close()

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        form = ArtistForm(request.form)
        newArtist = Artist(
            name=form.name.data,
            genres=form.genres.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data,
            website=form.website.data,
        )
        db.session.add(newArtist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for("show_artist", artist_id=newArtist.id))
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('Sorry an error occurred')
        return redirect(url_for("index"))
    finally:
        db.session.close()
    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    try:
        query = db.session.query(Show).join(Artist).join(Venue)
        shows = []
        for show in query:
            # foundArtist = Artist.query.get(show.artist_id)
            # foundVenue = Venue.query.get(show.venue_id)
            shows.append(
                {"venue_id": show.venue_id,
                 "venue_name": show.venue.name,
                 "artist_id": show.artist_id,
                 "artist_name": show.artist.name,
                 "artist_image_link": show.artist.image_link,
                 "start_time": show.start_time}
            )
        return render_template('pages/shows.html', shows=shows)
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Sorry! An error occured.")
        return redirect(url_for("index"))
    finally:
        db.session.close()


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        form = ShowForm(request.form)
        artist = form.artist_id.data
        if not Artist.query.get(artist):
            flash("Artist not found. Please try again")
            return redirect(url_for('create_show_submission'))

        venue = form.venue_id.data
        if not Venue.query.get(venue):
            flash("Venue not found. Please try again")
            return redirect(url_for('create_show_submission'))

        venueShowList = db.session.query(Show).filter_by(venue_id=venue).all()
        artistShowList = db.session.query(
            Show).filter_by(artist_id=artist).all()

        start_time = form.start_time.data

        if isDate(start_time):
            d1 = start_time
            # Check if venue is available for date
            if venueShowList:
                for show in venueShowList:
                    d2 = show.start_time
                    if d2 == d1:
                        flash("Sorry venue is already booked at date!")
                        return redirect(url_for('create_shows'))
            # Check if artist is available for date
            if artistShowList:
                for show in artistShowList:
                    d2 = show.start_time
                    if d2 == d1:
                        flash("Sorry artist is already booked at date!")
                        return redirect(url_for('create_shows'))
            newShow = Show(
                artist_id=artist,
                venue_id=venue,
                start_time=start_time
            )

            db.session.add(newShow)
            db.session.commit()
            flash("Show listed successfully!")
        else:
            flash(
                'Date format is not valid. Please use this syntax Year-Month-Day Hour:Minure:Seconds')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        print(sys.exc_info())
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#


def isDate(arg):
    isCorrect = False
    try:
        datetime.strftime(arg, '%Y-%m-%d %H:%M:%S')
        isCorrect = True
    except:
        isCorrect = False
        print("Arguement is not a date")
    finally:
        return isCorrect


# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
