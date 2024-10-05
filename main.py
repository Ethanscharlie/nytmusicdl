"""
Written by Ethanscharlie
https://github.com/Ethanscharlie
"""

import concurrent.futures
import json
import os
import re
import time
import moviepy.editor as mp
import mutagen
import requests
import wget
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
from mutagen.mp3 import MP3
from PIL import Image

VIDEO_FILE_EXT = "mp4"
AUDIO_FILE_EXT = "mp3"

def set_cover_art(audio_file_location: str, image_location: str):
    # Sets the album cover art of the file to the image

    audio = MP3(audio_file_location, ID3=ID3)

    audio.tags.add(APIC(
        mime='image/jpeg',
        type=3,
        desc=u'Cover',
        data=open(image_location, 'rb').read()
    ))

    audio.save()

def do_metadata(file: str, title: str, album: str, artist: str, index: int=1):
    ''' Sets the metadata (album name, title, art, etc.) for the mp3 file '''

    # Gets the audio in mutagen
    try:
        audio = EasyID3(file)
    except:
        try:
            audio = mutagen.File(file, easy=True)
            audio.add_tags()
        except:
            print(f"{bcolors.FAIL}There was an metadata error on {video_title}{bcolors.ENDC} -- {file}")
            return

    # Wipes and then sets each tag to the given input data
    audio.delete()
    audio['title'] = remove_topic_stuff(title)
    audio["album"] = album    
    audio['artist'] = artist
    audio['tracknumber'] = str(index)
    audio.save()

    # Cover art
    # img_file = get_cover_art(input_data['cover_art'], os.path.dirname(file))
    # if img_file: set_cover_art(file, img_file)

    return audio

def remove_topic_stuff(string: str) -> str:
    # Removes dumb YouTube things in names like - Topic, or Album -

    for text in CONFIG['autoremove']:
        if text in string:
            string = string.replace(text, "")

    print(string)
    return string
