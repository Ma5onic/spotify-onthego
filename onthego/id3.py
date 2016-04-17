import eyed3
import requests

def tag(filepath, track):
    """
    Tag an mp3 file with all the appropriate info, including downloaded album art.
    """
    audiofile = eyed3.load(filepath)
    audiofile.tag.artist = track.artist
    audiofile.tag.title = track.name
    audiofile.tag.album = track.album_name
    audiofile.date = track.album_release_date

    # Get album art image
    image_data = requests.get(track.album_art_url).content
    audiofile.tag.images.set(
        3,# 3 means 'front cover'
        image_data,
        "image/jpeg"
    )

    audiofile.tag.save()