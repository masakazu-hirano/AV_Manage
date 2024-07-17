import json
import logging
import os
import requests
import subprocess

from datetime import datetime
from Modules.SET_Environment import Read_Environment_File
from Modules.Spotify import SET_Spotify_Client
from spotipy.client import Spotify

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		notion_header_data: dict = {
			'accept': 'application/json',
			'content-type': 'application/json',
			'Notion-Version': '2022-06-28',
			'Authorization': f"Bearer {os.getenv('NOTION_API_TOKEN')}"
		}

		spotify_client: Spotify = SET_Spotify_Client()
		artist_id_list: tuple = (
			'3z8diLlUCkN1j9N9ZdnfBJ',	# NiziU
			'4SpbR6yFEvexJuaBpgAU5p',	# LE SSERAFIM
			'5R7AMwDeroq6Ls0COQYpS4'	# Kep1er
		)

		for artist_id in artist_id_list:
			artist_data: dict = {}
			spotify_artist_data: dict = spotify_client.artist(artist_id = artist_id)
			artist_data['アーティスト名'] = spotify_artist_data['name']

			album_data_list: dict = spotify_client.artist_albums(
				artist_id = artist_id,
				include_groups = 'single,album,compilation,appears_on',
				country = 'JP',
				limit = 50
			)['items']

			artist_data['アルバム一覧'] = []
			for spotify_album_data in album_data_list:
				artist_data['アルバム一覧'].append({
					'ID（アルバム）': spotify_album_data['id'],
					'公開日': datetime.strptime(spotify_album_data['release_date'], '%Y-%m-%d'),
					'アルバム画像': spotify_album_data['images'][0]['url']
				})

			artist_data["アルバム一覧"] = sorted(artist_data["アルバム一覧"], key=lambda album: album["公開日"])
			for album in artist_data['アルバム一覧']:
				spotify_track_list = spotify_client.album_tracks(
					album_id = album['ID（アルバム）'],
					market = 'JP',
					limit = 50
				)['items']

				for track in spotify_track_list:
					notion_db_list: str = requests.post(
						url = f"https://api.notion.com/v1/databases/{os.getenv('NOTION_DATABASE_ID')}/query",
						headers = notion_header_data,
						json = {
							'page_size': 100,
							'filter': {'and': [
								{
									'property': 'アーティスト',
									'select': {'equals': artist_data['アーティスト名']}
								},
								{
									'property': 'タイトル',
									'title': {'equals': track['name']}
								}
							]},

							'sorts': [{
								'property': '公開日',
								'direction': 'ascending'
							}]
						}
					).text

					if len(json.loads(s = notion_db_list)['results']) == 0:
						response = requests.post(
							url = f"https://api.notion.com/v1/pages",
							headers = notion_header_data,
							json = {
								'parent': {'database_id': os.getenv('NOTION_DATABASE_ID')},
								'icon': {'external': {'url': album['アルバム画像']}},
								'cover': {'external': {'url': album['アルバム画像']}},
								'properties': {
									'ID': {
										'rich_text': [{
											'text': {'content': track['id']}
										}]
									},

									'アーティスト': {
										'select' : {
											'name': artist_data['アーティスト名'],
											'color': 'gray'
										}
									},

									'タイトル': {
										'title': [{
											'text': {'content': track['name']}
										}]
									},

									'再生時間': {'number': track['duration_ms'] / 1000},
									'公開日': {
										'date': {
											'start': str(album['公開日'].date()),
											'end': None
										}
									}
								}
							}
						)

						subprocess.run(
							['spotdl', 'download', f"https://open.spotify.com/track/{track['id']}"]
						)
			break
		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')