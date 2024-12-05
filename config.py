from os import environ as env
from dotenv import load_dotenv

load_dotenv()

TOKEN = env['TOKEN']
MANIFEST_URL = env['MANIFEST_URL']
FRAGMENT_URL = env['FRAGMENT_URL']
WALLET_URL = env['WALLET_URL']
REDIRECT_URL = env['REDIRECT_URL']
YOOTOKEN = env['YOOMONEY_ACCESS_TOKEN']
TONKEEPER_ADDRESS = env['TONKEEPER_ADDRESS']