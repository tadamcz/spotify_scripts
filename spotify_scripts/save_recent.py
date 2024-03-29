import datetime
import os
import shelve

import spotipy
from dotenv import load_dotenv
from spotipy import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

if os.getenv("GIT_REV") is not None:  # In Dokku environment
    ROOT_DIR = "/persist/spotify_scripts"  # Mount this directory to a persistent volume
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

if __name__ == "__main__":
    # You should run this script periodically. You can only get the 50 most recent tracks from the API,
    # so you should run this script frequently enough (e.g. every hour)

    load_dotenv()

    def print_playlist_count(playlist_id):
        playlist = spt.playlist(playlist_id)
        print(f"Playlist '{playlist['name']}' has {playlist['tracks']['total']} tracks")

    pwd = os.path.dirname(os.path.realpath(__file__))
    spt = spotipy.Spotify(
        client_credentials_manager=SpotifyOAuth(
            scope=[
                "user-read-recently-played",
                "playlist-modify-private",
                "playlist-read-private",
            ],
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            # If you choose a http-scheme URL, and it’s for localhost or 127.0.0.1, AND it specifies a port,
            # then spotispy will instantiate a server on the indicated response to receive the access token from the
            # response at the end of the oauth flow
            redirect_uri="http://127.0.0.1:9090",
            cache_handler=CacheFileHandler(cache_path=f"{ROOT_DIR}/.credentials_cache"),
        )
    )

    # The 'recently played' playlist
    playlist_id = os.getenv("RECENTLY_PLAYED_PLAYLIST_ID")
    playlist = spt.playlist(playlist_id)

    # Load from disk
    with shelve.open(f"{ROOT_DIR}/data.db") as db:
        saved_up_to = db.get(
            "saved_up_to", datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        )
        print(f"Disk says we saved tracks up to {saved_up_to} to playlist '{playlist['name']}'")

    # Get recently played tracks and build list of tracks to add
    print("Getting new recently played tracks...")
    recent = spt.current_user_recently_played(limit=50)[
        "items"
    ]  # They only let you get the 50 most recent tracks
    print(f"Most recent track '{recent[0]['track']['name']}' played at {recent[0]['played_at']}")

    tracks_to_add = []
    for track in recent:
        track_played_at = datetime.datetime.fromisoformat(track["played_at"])
        if track_played_at > saved_up_to:
            tracks_to_add.append(track)

    # Delete tracks from playlist if we have too many
    # Rough order of magnitude for downloads on 'very high' quality: 1000 tracks = 10 GB
    MAX_PLAYLIST_TRACKS = 1500

    print_playlist_count(playlist_id)
    n_tracks_to_delete = max(
        playlist["tracks"]["total"] + len(tracks_to_add) - MAX_PLAYLIST_TRACKS, 0
    )
    if n_tracks_to_delete > 0:
        print(
            f"Need to delete {n_tracks_to_delete} tracks from playlist (MAX_PLAYLIST_TRACKS={MAX_PLAYLIST_TRACKS})..."
        )
        tracks_to_delete = spt.playlist_items(playlist_id, limit=n_tracks_to_delete)["items"]
        for index, track in enumerate(tracks_to_delete):
            tracks_to_delete[index] = {"uri": track["track"]["uri"], "positions": [index]}
        spt.playlist_remove_specific_occurrences_of_items(playlist_id, tracks_to_delete)
        print_playlist_count(playlist_id)

    if len(tracks_to_add) <= 0:
        print("No new tracks to add")
    else:
        # Add tracks to playlist
        print(f"Adding {len(tracks_to_add)} tracks to playlist")
        if len(tracks_to_add) >= 50:
            print(
                "WARNING: Maxed out the 50 track limit for recent tracks, you likely missed some tracks! It's "
                "recommended to run the script more frequently."
            )
        track_ids = [track["track"]["id"] for track in tracks_to_add]
        spt.playlist_add_items(playlist_id, track_ids)
        print_playlist_count(playlist_id)

        # Save to disk
        with shelve.open(f"{ROOT_DIR}/data.db") as db:
            saved_up_to = tracks_to_add[0]["played_at"]
            saved_up_to = datetime.datetime.fromisoformat(saved_up_to)
            print(f"Saved tracks up to {saved_up_to} to playlist, writing datetime to disk...")
            db["saved_up_to"] = saved_up_to
