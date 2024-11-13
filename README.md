![logo](https://github.com/user-attachments/assets/452a127d-b760-4e41-9a83-5c47f4c74df6)

The idea behind this project is that the script shouldn't be broken when the youtube content provider goes down. In this setup we use deezer to gather all the album information and then use that data to individually download each song from yt-dlp.

### Dependences
`pip install -r requirements.txt`

You will also need to install **yt-dlp** (![Install](https://github.com/yt-dlp/yt-dlp/wiki/Installation))

### Usage
`python3 nytmusicdl.py "Search album q here" ~/Downloads`
