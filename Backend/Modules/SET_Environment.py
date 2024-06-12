from dotenv import load_dotenv

def Read_Environment_File() -> bool:
	return load_dotenv(
		dotenv_path = './Backend/.env',
		encoding = 'utf-8',
		override = True,
		verbose = True
	)