import logging
import spotipy

from Modules.SET_Environment import Read_Environment_File
from spotipy.oauth2 import SpotifyOAuth

if __name__ == '__main__':
	logging.basicConfig(
		level = logging.INFO,
		format = '[{levelname}]: {message}',
		style = '{'
	)

	if Read_Environment_File() == True:
		logging.info(msg = '処理が正常に終了しました。')
	else:
		logging.error(msg = '環境変数（.env）の読み込みに失敗しました。')