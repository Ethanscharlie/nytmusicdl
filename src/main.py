"""
Written by Ethanscharlie
https://github.com/Ethanscharlie
"""

import concurrent.futures
import json
import os
from os import path
import re
import time
import moviepy.editor as mp
import mutagen
import requests
import wget

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

from PIL import Image

from AlbumInfo import AlbumInfo

VIDEO_FILE_EXT = "mp4"
AUDIO_FILE_EXT = "mp3"



def get_tracklist(url: str):
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(responses.status_code)
    
    return [track["title"] for track in response.json()["data"]] 

def search_music(search_term: str) -> [AlbumInfo]:
    url = f"https://api.deezer.com/search?q={search_term}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(responses.status_code)

    data = response.json()
    responses = []

    item = data.get('data', [])[0]
    album_name = item.get('album', {}).get('title', 'N/A')
    artist_name = item.get('artist', {}).get('name', 'N/A')
    cover_art = item.get('album', {}).get('cover_big', 'N/A')  # Use cover_big for higher quality

    tracklist = get_tracklist(item["album"]["tracklist"])
    responses.append(AlbumInfo(album_name, artist_name, cover_art, tracklist))

    return responses


query = "phobia breaking benjamin"

album_info = search_music(query)[0]
album_info.download("Downloads")
