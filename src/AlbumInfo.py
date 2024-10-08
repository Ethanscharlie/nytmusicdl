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


class AlbumInfo:
    def __init__(self, album: str, artist: str, cover_art_url: str, tracklist: [str]):
        self.album = album
        self.artist = artist
        self.tracklist = tracklist
        self.cover_art_url = cover_art_url

    def download(self, folder: path):
        download_start_time = time.time()

        self.cover_path = self._AlbumInfo__get_cover_art(self.cover_art_url, folder)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for index, track_name in enumerate(self.tracklist):
                executor.submit(self.download_and_assign_metadata_to_song, folder, track_name, index)

        download_time = time.time() - download_start_time
        print(f"Download took {download_time:.2f} seconds")

    def download_and_assign_metadata_to_song(self, folder: path, track_name: str, index: int):
        track_url = self.search_song(f"{track_name} by {self.artist}, {self.album}")
        self._AlbumInfo__download_video(track_url, track_name, folder)
        self._AlbumInfo__assign_metadata_to_file(path.join(folder, f"{track_name}.mp3"), track_name, index+1)

    def __assign_metadata_to_file(self, file: str, title: str, index: int=1):
        ''' Sets the metadata (album name, title, art, etc.) for the mp3 file '''
    
        audio = EasyID3(file)
    
        audio.delete()
        audio['title'] = title
        audio["album"] = self.album    
        audio['artist'] = self.artist
        audio['tracknumber'] = str(index)
        audio.save()
    
        if self.cover_path:
            self._AlbumInfo__set_cover_art(file, self.cover_path)
    
        return audio

    def search_song(self, query):
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(search_url)
    
        # Regular expression to find video links
        pattern = r'watch\?v=(.*?)"'
        video_links = re.findall(pattern, response.text)
    
        if not video_links:
            raise Exception(f"Video not found at url {search_url}")
            
        return f"https://www.youtube.com/watch?v={video_links[0][:-1]}"

    def __set_cover_art(self, audio_file_location: str, image_location: str):
        # Sets the album cover art of the file to the image
    
        audio = MP3(audio_file_location, ID3=ID3)
    
        audio.tags.add(APIC(
            mime='image/jpeg',
            type=3,
            desc=u'Cover',
            data=open(image_location, 'rb').read()
        ))
    
        audio.save()
    
    def __get_cover_art(self, url: str, directory: str) -> path:
        # Grabs and downloads the cover art after figuring out if it's a location, or a web image
    
        target_location = os.path.join(directory, 'cover.jpg')
    
        if not requests.get(url).status_code:
            raise Exception("Image not found :(")
    
        img_file = wget.download(url, directory)
        image = Image.open(img_file)
    
        # Save
        image.save(target_location)
        os.remove(img_file)
    
        return target_location

    def __download_video(self, url: str, filename: str, folder: path) -> None:
        current_directory = os.getcwd()
        os.system(f"cd {folder}")

        command = f'yt-dlp -x --audio-format mp3 -o "{folder}/{filename}.%(ext)s" {url}'
        print(command)
        os.system(command)

        os.system(f"cd {current_directory}")
