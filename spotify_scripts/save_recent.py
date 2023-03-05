import datetime
import os
import shelve

import spotipy
from dotenv import load_dotenv
from spotipy import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

from spotify_scripts.log import Tee

if __name__ == "__main__":
    # You should run this script periodically. You can only get the 50 most recent tracks from the API,
    # so you should run this script frequently enough (e.g. every hour)
    with Tee(f"logs/{datetime.datetime.now().isoformat()}_save_recent.log"):
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
                cache_handler=CacheFileHandler(cache_path=f"{pwd}/.cache"),  # Absolute path
            )
        )

        # The 'recently played' playlist
        playlist_id = os.getenv("RECENTLY_PLAYED_PLAYLIST_ID")
        playlist = spt.playlist(playlist_id)

        # Load from disk
        with shelve.open("data.db") as db:
            saved_up_to = db.get(
                "saved_up_to", datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
            )
            print(f"Disk says we saved tracks up to {saved_up_to} to playlist '{playlist['name']}'")

        # Get recently played tracks and build list of tracks to add
        print("Getting new recently played tracks...")
        recent = spt.current_user_recently_played(limit=50)[
            "items"
        ]  # They only let you get the 50 most recent tracks
        print(
            f"Most recent track '{recent[0]['track']['name']}' played at {recent[0]['played_at']}"
        )

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
            track_ids = [track["track"]["id"] for track in tracks_to_add]
            spt.playlist_add_items(playlist_id, track_ids)
            print_playlist_count(playlist_id)

            # Save to disk
            with shelve.open("data.db") as db:
                saved_up_to = tracks_to_add[0]["played_at"]
                saved_up_to = datetime.datetime.fromisoformat(saved_up_to)
                print(f"Saved tracks up to {saved_up_to} to playlist, writing datetime to disk...")
                db["saved_up_to"] = saved_up_to
                print(f"Writing {len(tracks_to_add)} tracks to disk...")
                key = f"tracks_savepoint_{saved_up_to.isoformat()}"
                db[key] = tracks_to_add

        # Print shelf size
        print(f"Shelf size: {os.path.getsize('data.db') / 1024 / 1024} MB")
