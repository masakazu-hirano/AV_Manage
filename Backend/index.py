import boto3
import logging
import os
import requests
import spotipy

from botocore.config import Config
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

def Read_Environment_File() -> bool:
	return load_dotenv(
		dotenv_path = './Backend/.env',
		encoding = 'utf-8',
		override = True,
		verbose = True
	)

def Create_Spotify_Client() -> Spotify:
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

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		spotify_client: Spotify = Create_Spotify_Client()

		artist_information: dict = spotify_client.artist(artist_id = '')
		artist_name: str = artist_information['name']
		artist_image_url: str = artist_information['images'][0]['url']

		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')