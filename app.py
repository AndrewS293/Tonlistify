from flask import Flask, redirect, request, session, url_for, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables from .env file
load_dotenv()

# Configure Spotify OAuth
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "user-read-recently-played user-top-read playlist-read-collaborative playlist-read-private user-library-read playlist-modify-private playlist-modify-public"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    )


@app.route('/')
def index():
    return render_template('login.html')




@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    print(session["token_info"])

    return redirect(url_for('profile'))


@app.route('/profile')
def profile():
    token_info = session.get("token_info")
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])

    # Fetch the user's profile
    user_profile = sp.current_user()

    # Print the entire user profile for debugging purposes
    print("User Profile Data:", user_profile)

    profile_image_url = user_profile['images'][0]['url'] if user_profile['images'] else None


    return render_template('main.html', profile_image_url=profile_image_url, user_profile=user_profile)




@app.route('/top-tracks')

#create option to change time_range preferably without making new page

def top_tracks():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])

    track_list = "<ul>"

    for i in range(0, 401, 50):
        recent_tracks = sp.current_user_top_tracks(limit=50, offset=i, time_range='medium_term')

        for track in recent_tracks['items']:
            track_list += f"<li>{track['name']} by {track['artists'][0]['name']} -> {track['popularity']}</li>"


    track_list += "</ul>"

    return f'''
        <h2>Your Top Tracks</h2>
        {track_list}
        <p><a href="/">Home</a></p>
    '''


@app.route('/top-artists')

#time_range option, also have popularity?

def top_artists():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])
    top_artists = sp.current_user_top_artists(limit=50, time_range='short_term')

    track_list = "<ul>"
    for track in top_artists['items']:
        track_list += f"<li>{track['name']} -> {track['genres']} -> {track['popularity']}</li>"


    track_list += "</ul>"

    return f'''
        <h2>Your Top Tracks</h2>
        {track_list}
        <p><a href="/">Home</a></p>
    '''


@app.route('/recent-tracks')

#time_range option - choose above or below x

def recent_tracks():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])

    track_listA = "<ul>"
    track_listB = "<ul>"
    track_listC = "<ul>"


    for i in range(0, 401, 50):
        recent_tracks = sp.current_user_top_tracks(limit=50, offset=i, time_range='short_term')

        for track in recent_tracks['items']:
            if track['popularity'] > 60:
                track_listA += f"<li>{track['name']} by {track['artists'][0]['name']} -> {track['popularity']}</li>"
            elif track['popularity'] < 30:
                track_listB += f"<li>{track['name']} by {track['artists'][0]['name']} -> {track['popularity']}</li>"
            else:
                track_listC += f"<li>{track['name']} by {track['artists'][0]['name']} -> {track['popularity']}</li>"

    track_listA += "</ul>"
    track_listB += "</ul>"
    track_listC += "</ul>"

    return f'''
        <h2>Popular Tracks</h2>
        {track_listA}
        <br></br>
        <br></br>
        <h2>Mid Tracks</h2>
        {track_listC}
        <br></br>
        <br></br>
        <h2>'Indie' Tracks</h2>
        {track_listB}
        <p><a href="/">Home</a></p>
    '''


@app.route('/average_popularity')
def average_popularity():

    #choose number of songs to average by - time range

    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])


    popularity = 0
    x = 1.5
    for i in range(0, 401, 50):
        top_tracks = sp.current_user_top_tracks(limit=50, offset=i, time_range='short_term')
        for track in top_tracks['items']:
            popularity += track['popularity'] * x
            x -= .0025
    popularity /= 400

    print(popularity)
    return f'<h2>Balanced Average Popularity of Your Top Songs is {popularity}</h2>'



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])


    playlist_name = "Playlist"
    min_pop = 0
    max_pop = 0
    track_list = ""

    tracks = sp.current_user_top_tracks()
    for track in tracks['items']:
        track_list += f"<li>{track['name']} by {track['artists'][0]['name']} </li>"

    if request.method == 'POST':
        playlist_name = request.form.get('playlist_name')
        min_pop = request.form.get('min_pop')
        max_pop = request.form.get('max_pop')
        time_range = request.form.get('time_range')
        max_songs = request.form.get('max_songs')



        user_id = sp.current_user()['id']

        track_list = ""
        i = 0
        j = 0

        # Create a new playlist
        playlist = sp.user_playlist_create(user=user_id,
                                           name=playlist_name,
                                           public=False)



        while True:
            checked_tracks = sp.current_user_top_tracks(limit=20, offset=i, time_range=time_range)

            track_ids = [track['id'] for track in checked_tracks['items'] if track['popularity'] > int(min_pop) and track['popularity'] < int(max_pop)]


            sp.playlist_add_items(playlist_id=playlist["id"], items=track_ids)

            i += 20
            j += len(track_ids)

            for track in checked_tracks['items']:
                if track['popularity'] > int(min_pop) and track['popularity'] < int(max_pop):
                    track_list += f"<li>{track['name']} by {track['artists'][0]['name']} </li>"

            if j < int(max_songs):
                continue
            else:
                break





    return render_template('create_playlist.html', name = playlist_name, track_list=track_list)


#create a page that creates 3-4 playlists for current user (preferably checks if they already exist) then adds the most popular ones into a playlist, mid pop. ones into a playlist, ect.
#if they already exist, delete everything and replace. use their top 300-500 top songs (they choose time period?)
#cache system?? lord save me


@app.route('/recommendation')
def recommendation():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect('/')

    sp = Spotify(auth=token_info['access_token'])
    joe = ""

    for i in range(0, 5, 1):
        #seed_tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')
        #track_ids = [track['id'] for track in seed_tracks['items']]
        seed_artists = sp.current_user_top_artists(time_range='short_term')
        artist_ids = [artist['id'] for artist in seed_artists['items']]
        bob = sp.recommendations(seed_artists=artist_ids[:5], max_popularity=30) #seed_tracks=track_ids[:5]

        recommended_tracks = bob['tracks']

        # Prepare the recommendations for display
        recommendation_list = []
        for track in recommended_tracks:
            track_info = f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}"
            recommendation_list.append(track_info)


        joe += "<br>".join(recommendation_list)

    UserID = sp.current_user()["id"]

    createdPlaylist = sp.user_playlist_create(UserID, "Recommended")

    track_ids = [track['id'] for track in recommended_tracks]

    sp.playlist_add_items(playlist_id=createdPlaylist["id"], items=track_ids)

    return joe

#add a recommendation page: also adds songs to playlists?


if __name__ == "__main__":
    app.run(debug=True)
