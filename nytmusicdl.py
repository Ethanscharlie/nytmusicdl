#!/usr/bin/env python3

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
import sys

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

from PIL import Image

VIDEO_FILE_EXT = "mp4"
AUDIO_FILE_EXT = "mp3"
PLAYLIST_FILTER = "&sp=EgIQAw%253D%253D"


def download(
    album: str, artist: str, cover_art_url: str, tracklist: list[str], folder: str
):
    download_start_time = time.time()

    # Find a playlist and get the list of video urls
    yt_urls: list[str] = []
    query = f"{album} {artist}"
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}{PLAYLIST_FILTER}"
    response = requests.get(search_url)

    pattern = r'playlist\?list=(.*?)"'
    playlist_links = re.findall(pattern, response.text)

    if not playlist_links:
        raise Exception(f"Nothing not found at search url {playlist_links}")

    print(playlist_links)

    for id in playlist_links:
        playlist_url = f"https://www.youtube.com/playlist?list={id}"
        print(playlist_url)

        response = requests.get(playlist_url)

        start_index = response.text.index(r"")
        end_index = response.text.index(r"innertubeCommand")
        list_text = response.text[start_index:end_index]

        yt_urls = []
        video_pattern = r'watch\?v=(.*?)"'
        video_ids = re.findall(video_pattern, list_text)

        if not video_ids:
            raise Exception(f"No watch links found on playlist page")

        for id in video_ids:
            # Filter out
            AndIndex = id.find("\\u0026")
            if AndIndex == -1:
                continue
            id = id[:AndIndex]

            video_url = f"https://www.youtube.com/watch?v={id}"
            print(video_url)
            yt_urls.append(video_url)

        if len(yt_urls) > len(tracklist):
            print(f"Playlist is too long, yt_urls: {len(yt_urls)}, tracklist: {len(tracklist)}")
            yt_urls = []
            continue
        else:
            break

    if len(yt_urls) == 0:
        raise Exception("No good playlists found")

    # Download the album cover art
    target_location = os.path.join(folder, "cover.jpg")

    if not requests.get(cover_art_url).status_code:
        raise Exception("Image not found :(")

    img_file = wget.download(cover_art_url, folder)
    image = Image.open(img_file)

    # Save
    image.save(target_location)
    os.remove(img_file)

    cover_path = target_location

    print("\n")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for index, track_name in enumerate(tracklist):
            def download_and_assign_metadata_to_song(index: int, track_name: str):
                track_url = yt_urls[index]
                print(f"Name: {track_name}, Url: {track_url}, index: {index}")

                # Download video
                current_directory = os.getcwd()
                os.system(f"cd '{folder}'")

                command = f'yt-dlp -x --audio-format mp3 -o "{folder}/{track_name}.%(ext)s" {track_url}'
                print(command)
                os.system(command)
                os.system(f"cd '{current_directory}'")

                # Assign metadata
                audio_file = path.join(folder, f"{track_name}.mp3")
                tracknumer = index + 1

                audio = EasyID3(audio_file)

                audio.delete()
                audio["title"] = track_name
                audio["album"] = album
                audio["artist"] = artist
                audio["tracknumber"] = str(tracknumer)
                audio.save()

                # Set Cover art
                if cover_path:
                    id3audio = MP3(audio_file, ID3=ID3)
                    id3audio_tags: mutagen.id3.ID3 = id3audio.tags
                    id3audio_tags.add(
                        APIC(
                            mime="image/jpeg",
                            type=3,
                            desc="Cover",
                            data=open(cover_path, "rb").read(),
                        )
                    )
                    id3audio.save()

            executor.submit(download_and_assign_metadata_to_song, index, track_name)

    download_time = time.time() - download_start_time
    print(f"Download took {download_time:.2f} seconds")


def get_tracklist(url: str):
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(response.status_code)

    tracklist = []
    for track in response.json()["data"]:
        trackname = track["title"]

        if not trackname:
            continue

        if not len(trackname) > 0:
            continue

        trackname = trackname.replace(r"/", "|")
        tracklist.append(trackname)
        print(trackname)

    print(tracklist)
    return tracklist


def search_music(search_term: str) -> list[tuple[str, str, str, list[str]]]:
    url = f"https://api.deezer.com/search?q={search_term}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(response.status_code)

    data = response.json()
    responses = []

    item = data.get("data", [])[0]
    album_name = item.get("album", {}).get("title", "N/A")
    artist_name = item.get("artist", {}).get("name", "N/A")
    cover_art = item.get("album", {}).get(
        "cover_big", "N/A"
    )  # Use cover_big for higher quality

    tracklist = get_tracklist(item["album"]["tracklist"])
    responses.append((album_name, artist_name, cover_art, tracklist))

    return responses


def general_filter(text: str) -> str:
    text = text.replace("/", "-")
    text = text.replace(r"\\", "-")
    text = text.replace("&", "and")
    text = text.replace(":", " -")
    text = text.replace(",", " -")
    text = text.replace('"', " ")
    text = text.replace("'", " ")
    text = text.replace("?", " ")
    text = text.replace("*", " ")
    text = text.replace("<", "(")
    text = text.replace(">", ")")
    text = text.replace("|", "-")
    return text


def main():
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("""usage: nytmusicdl.py ALBUMSEARCH <-- ex: \"Phobia Breaking Benjamin\"

-a: Flag for downloading every album from an artist
usage: nytmusicdl.py -a ARTISTSEARCH <-- ex: \"Breaking Benjamin\"""")

    elif sys.argv[1] == "-a":
        artist_name_search = sys.argv[2]
        url = f"https://api.deezer.com/search/artist?q={artist_name_search}"
        response = requests.get(url)
        artist_name = general_filter(response.json().get("data", [])[0]["name"])
        print(f"Artist Name: {artist_name}")
        artist_id = response.json().get("data", [])[0]["id"]

        url = f"https://api.deezer.com/artist/{artist_id}/albums?limit=1000"
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(response.status_code)

        data = response.json()

        for album_data in data.get("data", []):
            album_name = general_filter(album_data["title"])
            cover_art = album_data["cover_big"]
            tracklist = get_tracklist(album_data["tracklist"])

            directory = sys.argv[3]

            artist_path = path.join(directory, artist_name)
            if not path.isdir(artist_path):
                os.mkdir(artist_path)

            album_path = path.join(artist_path, album_name)
            if not path.isdir(album_path):
                os.mkdir(album_path)

            try:
                download(album_name, artist_name, cover_art, tracklist, album_path)
            except Exception:
                print("WARNING A PLAYLIST COULD NOT BE FOUND")

    else:
        album_name, artist_name, cover_art, tracklist = search_music(sys.argv[1])[0]

        directory = sys.argv[2]

        artist_path = path.join(directory, artist_name)
        if not path.isdir(artist_path):
            os.mkdir(artist_path)

        album_path = path.join(artist_path, album_name)
        if not path.isdir(album_path):
            os.mkdir(album_path)

        download(artist_name, album_name, cover_art, tracklist, album_path)


main()
