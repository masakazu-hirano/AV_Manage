import logging
import os

import boto3
import requests
import spotipy

from io import BytesIO

from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
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

def Create_Boto3_Client():
	return  boto3.client(
		service_name = 's3',
		endpoint_url = f"https://{os.getenv('R2_BUCKET_URL')}.r2.cloudflarestorage.com",
		aws_access_key_id = os.getenv('R2_ACCESS_KEY_ID'),
		aws_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY'),
		config = Config(signature_version = 'v4')
	)

def Upload_Artist_Profile_Image(client, file_name: str) -> None:
	try:
		client.head_object(
			Bucket = 'av-manage',
			Key = f"NiziU/{file_name}"
		)
	except ClientError:
		client.upload_file(
			Filename = f"./Backend/Downloads/{file_name}",
			Bucket = 'av-manage',
			Key = f"{artist_name}/{artist_name}_{artist_image_url.split(sep = '/')[-1]}.png",
		)

		logging.info(msg = f"ファイルアップロード完了: {file_name}")
	os.remove(path = f"./Backend/Downloads/{file_name}")

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		s3_client = Create_Boto3_Client()
		spotify_client: Spotify = Create_Spotify_Client()

		artist_information: dict = spotify_client.artist(artist_id = '3z8diLlUCkN1j9N9ZdnfBJ')
		artist_name: str = artist_information['name']
		artist_image_url: str = artist_information['images'][0]['url']

		file_name: str = f"{artist_name}_{artist_image_url.split(sep = '/')[-1]}.png"
		with Image.open(
			fp = BytesIO(initial_bytes = requests.get(url = artist_image_url).content),
			mode = 'r',
			formats = ('BMP', 'GIF', 'JPEG', 'PNG', 'WEBP')
		) as image_file:
			image_file.save(
				fp = f"./Backend/Downloads/{file_name}",
				format = 'PNG',
				compress_level = 0,
				optimize = False
			)

		Upload_Artist_Profile_Image(s3_client, file_name)
		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')