import json
import logging
import os
import requests

from io import BytesIO
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime
from PIL import Image
from spotipy.client import Spotify

from Modules.SET_Environment import Read_Environment_File
from Modules.Cloudflare import SET_R2_Client
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

def GET_Artist_Data(client: Spotify, artist_id_list: tuple) -> list:
	artist_list: list = []
	for artist_id in artist_id_list:
		artist_data: dict = client.artist(artist_id = artist_id)
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

	return artist_list

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		r2_client = SET_R2_Client()
		spotify_client: Spotify = SET_Spotify_Client()
		notion_header_data: dict = {
			'accept': 'application/json',
			'content-type': 'application/json',
			'Notion-Version': '2022-06-28',
			'Authorization': f"Bearer {os.getenv('NOTION_API_TOKEN')}"
		}

		artist_id_list: tuple = ('3z8diLlUCkN1j9N9ZdnfBJ', '4SpbR6yFEvexJuaBpgAU5p', '5R7AMwDeroq6Ls0COQYpS4')
		artist_list: list = GET_Artist_Data(spotify_client, artist_id_list)
		for artist in artist_list:
			artist_image_file: str = f"{artist.name[0]}_{artist.image_url.split(sep = '/')[-1]}.png"
			with Image.open(
				fp = BytesIO(initial_bytes = requests.get(url = artist.image_url).content),
				mode = 'r',
				formats = ('BMP', 'GIF', 'JPEG', 'PNG', 'WEBP')
			) as image_file:
				image_file.save(
					fp = f"./Backend/Downloads/{artist_image_file}",
					format = 'PNG',
					compress_level = 0,
					optimize = False
				)

			try:
				r2_client.head_object(
					Bucket = 'av-manage',
					Key = f"{artist.name[0]}/images/{artist_image_file}"
				)
			except ClientError:
				r2_client.upload_file(
					Filename = f"./Backend/Downloads/{artist_image_file}",
					Bucket = 'av-manage',
					Key = f"{artist.name[0]}/images/{artist_image_file}",
				)

				logging.info(msg = f"ファイルアップロード完了: {artist_image_file}")
			os.remove(path = f"./Backend/Downloads/{artist_image_file}")

		for artist in artist_list:
			album_data_list: dict = spotify_client.artist_albums(
				artist_id = artist.id[0],
				include_groups = 'single,album,compilation,appears_on',
				limit = 50,
				country = 'JP'
			)

			album_list: list = []
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
				album_image_file: str = f"{artist.name[0]}_{album.name[0]}_{artist.image_url.split(sep = '/')[-1]}.png"
				with Image.open(
					fp = BytesIO(initial_bytes = requests.get(url = album.image_url).content),
					mode = 'r',
					formats = ('BMP', 'GIF', 'JPEG', 'PNG', 'WEBP')
				) as image_file:
					image_file.save(
						fp = f"./Backend/Downloads/{album_image_file}",
						format = 'PNG',
						compress_level = 0,
						optimize = False
					)

				try:
					r2_client.head_object(
						Bucket = 'av-manage',
						Key = f"{artist.name[0]}/images/album/{album_image_file}"
					)
				except ClientError:
					r2_client.upload_file(
						Filename = f"./Backend/Downloads/{album_image_file}",
						Bucket = 'av-manage',
						Key = f"{artist.name[0]}/images/album/{album_image_file}",
					)

					logging.info(msg = f"ファイルアップロード完了: {album_image_file}")
				os.remove(path = f"./Backend/Downloads/{album_image_file}")

			for album in album_list:
				track_data_list = spotify_client.album_tracks(
					album_id = album.id[0],
					limit = 50,
					market = 'JP'
				)

				for track_data in track_data_list['items']:
					notion_db_list: str = requests.post(
						url = f"https://api.notion.com/v1/databases/{os.getenv('NOTION_DATABASE_ID')}/query",
						headers = notion_header_data,
						json = {
							'filter': {'and': [
								{
									'property': 'アーティスト',
									'multi_select': {'contains': artist.name[0]}
								},
								{
									'property': 'アーティスト',
									'multi_select': {'contains': 'Spotify'}
								},
								{
									'property': 'タイトル',
									'title': {'equals': track_data['name']}
								}
							]},

							'sorts': [{
								'property': '公開日',
								'direction': 'ascending'
							}],

							'page_size': 100
						}
					).text

					if len(json.loads(s = notion_db_list)['results']) == 0:
						requests.post(
							url = f"https://api.notion.com/v1/pages",
							headers = notion_header_data,
							json = {
								'parent': {'database_id': os.getenv('NOTION_DATABASE_ID')},
								'icon': {'external': {'url': album.image_url}},
								'cover': {'external': {'url': album.image_url}},
								'properties': {
									'ID': {
										'rich_text': [{
											'text': {'content': track_data['id']}
										}]
									},

									'アーティスト': {
										'multi_select' :[{
											'name': artist.name[0],
											'color': 'gray'
										},
										{
											'name': 'Spotify',
											'color': 'gray'
										}]
									},

									'タイトル': {
										'title': [{
											'text': {'content': track_data['name']}
										}]
									},

									'再生時間': {'number': track_data['duration_ms'] / 1000},
									'公開日': {
										'date': {
											'start': str(album.release_date[0].date()),
											'end': None
										}
									}
								}
							}
						)

		r2_client.close()
		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')