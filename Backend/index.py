import logging
import os

import boto3
import requests

from io import BytesIO
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime
from PIL import Image
from spotipy.client import Spotify

from Modules.SET_Environment import Read_Environment_File
from Modules.Spotify import SET_Spotify_Client

class Artist:
	def __init__(self, id: str, name: str, genres: str, popularity: int, followers: int, image_url: str):
		self.id = id,
		self.name = name,
		self.genres = genres,
		self.popularity = popularity,
		self.followers = followers,
		self.image_url = image_url

class Album:
	def __init__(self, id: str, album_type: str, name: str, release_date: datetime, image_url: str):
		self.id = id,
		self.type = album_type,
		self.name = name,
		self.release_date = release_date,
		self.image_url = image_url

def Create_Boto3_Client():
	return  boto3.client(
		service_name = 's3',
		endpoint_url = f"https://{os.getenv('R2_BUCKET_URL')}.r2.cloudflarestorage.com",
		aws_access_key_id = os.getenv('R2_ACCESS_KEY_ID'),
		aws_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY'),
		config = Config(signature_version = 'v4')
	)

def Upload_Artist_Profile_Image(client, artist: Artist, file_name: str) -> None:
	try:
		client.head_object(
			Bucket = 'av-manage',
			Key = f"{artist.name[0]}/{file_name}"
		)
	except ClientError:
		client.upload_file(
			Filename = f"./Backend/Downloads/{file_name}",
			Bucket = 'av-manage',
			Key = f"{artist.name[0]}/{file_name}",
		)

		logging.info(msg = f"ファイルアップロード完了: {file_name}")

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		s3_client = Create_Boto3_Client()
		spotify_client: Spotify = SET_Spotify_Client()

		artist_id_list: tuple = ('3z8diLlUCkN1j9N9ZdnfBJ', '4SpbR6yFEvexJuaBpgAU5p', '5R7AMwDeroq6Ls0COQYpS4')
		artist_list: list = []
		for artist_id in artist_id_list:
			artist_data: dict = spotify_client.artist(artist_id = artist_id)
			artist_list.append(
				Artist(
					id = artist_data['id'],
					name = artist_data['name'],
					genres = artist_data['genres'][0],
					popularity = artist_data['popularity'],
					followers = artist_data['followers']['total'],
					image_url = artist_data['images'][0]['url']
				)
			)

		# for artist in artist_list:
		# 	file_name: str = f"{artist.name[0]}_{artist.image_url.split(sep = '/')[-1]}.png"
		# 	with Image.open(
		# 		fp = BytesIO(initial_bytes = requests.get(url = artist.image_url).content),
		# 		mode = 'r',
		# 		formats = ('BMP', 'GIF', 'JPEG', 'PNG', 'WEBP')
		# 	) as image_file:
		# 		image_file.save(
		# 			fp = f"./Backend/Downloads/{file_name}",
		# 			format = 'PNG',
		# 			compress_level = 0,
		# 			optimize = False
		# 		)

		# 	Upload_Artist_Profile_Image(s3_client, artist, file_name)
		# 	os.remove(path = f"./Backend/Downloads/{file_name}")

		album_list: list = []
		for artist in artist_list:
			album_data_list = spotify_client.artist_albums(
				artist_id = artist.id[0],
				include_groups = 'single,album,compilation,appears_on',
				limit = 50,
				country = 'JP'
			)

			for album_data in album_data_list['items']:
				album_list.append(
					Album(
						id = album_data['id'],
						album_type = album_data['album_type'],
						name = album_data['name'],
						release_date = datetime.strptime(album_data['release_date'], '%Y-%m-%d'),
						image_url = album_data['images'][0]['url']
					)
				)

		album_list = sorted(album_list, key = lambda x: x.release_date[0])
		for album in album_list:
			track_data_list = spotify_client.album_tracks(
				album_id = album.id[0],
				limit = 50,
				market = 'JP'
			)

			for track_data in track_data_list['items']:
				logging.info(msg = f"ID: {track_data['id']}")
				logging.info(msg = f"タイトル: {track_data['name']}")
				logging.info(msg = f"再生時間: {track_data['duration_ms'] / 1000}")
				break

			break
		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')