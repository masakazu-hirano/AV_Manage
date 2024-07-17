import os
import spotipy

from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

def SET_Spotify_Client() -> Spotify:
	return spotipy.Spotify(
		auth_manager = SpotifyClientCredentials(
			client_id = os.getenv(key = 'SPOTIFY_CLIENT_ID'),
			client_secret = os.getenv(key = 'SPOTIFY_CLIENT_SECRET_KEY'),
			requests_timeout = 30
		),

		language = 'ja',
		requests_timeout = 30,
		retries = 1
	)