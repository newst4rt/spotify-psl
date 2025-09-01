#!/usr/bin/env python
from time import sleep
import dbus
import requests
import json

max_lyric_line_len = 40

def c_print(text):
    print(" "*max_lyric_line_len*2, end="\r", flush=True)
    print(f'{text:<{max_lyric_line_len}}', end="\r", flush=True)

def get_track_data(spotify_metadata):
    spotify_metadata = spotify_metadata.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    ix = spotify_metadata["xesam:url"].rindex("/")
    artist = str(spotify_metadata["xesam:artist"][0])
    title = str(spotify_metadata["xesam:title"])
    return str(spotify_metadata["xesam:url"][ix+1:]), artist.replace(" ", "+"), title.replace(" ", "+")

def get_track_position(spotify_metadata):
    session_bus = dbus.SessionBus()
    spotify_bus = session_bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    properties_interface = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
    position = properties_interface.Get("org.mpris.MediaPlayer2.Player", "Position")

    position_seconds = position / 1_000.0

    return int(position_seconds)

def get_lyrics(artist, title):
    """ Get Lyrics from lrclib.net """
    url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}"
    header = {"User-Agent": "requests/*"}
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        body = response.json()
        lyric_data_formated = []
        tmp_lyric_data = body["syncedLyrics"].split("\n")
        for x in tmp_lyric_data:
            if x.startswith("["):
                sep_between_time_and_lyric = x.index("]")
                times = x[0+1:sep_between_time_and_lyric].split(":")
                lyric_line = x[sep_between_time_and_lyric+2:]
                ms = int(float(times[0])*60*1000 + float(times[1])*1000)
                lyric_data_formated.append({"startTimeMs": ms, "lyric_line": lyric_line})
        return lyric_data_formated
    
    elif response.status_code == 404:
        print(" $! ")
        return 404

def print_synced_lyric(lyric_data, time_pos):
    len_ly = len(lyric_data)
    for x in range(0, len_ly):
        if time_pos > int(lyric_data[x]["startTimeMs"]):
            if x == len_ly-1 or time_pos < int(lyric_data[x+1]["startTimeMs"]):
                p_lyric_line = lyric_data[x]["lyric_line"]
                if p_lyric_line:
                    c_print(f'{lyric_data[x]["lyric_line"]}')
                else:
                    c_print(f'♬')

if __name__ == "__main__":
    #try:
        session_bus = dbus.SessionBus()
        spotify_bus = session_bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        spotify_metadata = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")

        id = "initial"

        while True:
            track_id, artist, title = get_track_data(spotify_metadata)

            #Fetch lyrics only when the track has changed
            if track_id != id:
                c_print("↻")
                lyric_data = get_lyrics(artist, title)
                id, artist, title = get_track_data(spotify_metadata)
                c_print(f'♬')
                
            if lyric_data != 404:
                time_pos = get_track_position(spotify_metadata)
                if not lyric_data:
                    c_print("❌")
                    sleep(2)
                else: 
                    print_synced_lyric(lyric_data, time_pos)
            else:
                sleep(0.5)

            sleep(0.2)
