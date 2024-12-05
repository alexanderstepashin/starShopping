from bs4 import BeautifulSoup
from argparse import ArgumentParser
import requests
import json
import urllib.request


arg_parser = ArgumentParser()
arg_parser.add_argument(
    '--username'
)
username = arg_parser.parse_args().username


def get_html(url, params=None):
    r = requests.get(url, params=params)
    return r


def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def check_username(username):
    url = f'https://t.me/{username}'
    html = get_html(url)
    source = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source, 'html.parser')
    if html.status_code == 200:
        if not len(soup.find_all('div', class_='tgme_page_additional')):
            return False
        else:
            return True
    else:
        return False
