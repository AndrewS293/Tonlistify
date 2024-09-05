from flask import Flask, redirect, request, session, url_for, render_template, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import random

from unicodedata import category

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables from .env file
load_dotenv()

# Configure Spotify OAuth
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")



@app.route('/')
def index():
    return render_template('login.html')




@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-recently-played user-top-read playlist-read-collaborative playlist-read-private user-library-read playlist-modify-private playlist-modify-public",
        cache_path='.spotify_cache'
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-recently-played user-top-read user-read-email playlist-read-collaborative playlist-read-private user-library-read playlist-modify-private playlist-modify-public",
        cache_path='.spotify_cache'
    )
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    return redirect('/create_playlist')


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

if __name__ == '__main__':
    app.run(debug=True)
