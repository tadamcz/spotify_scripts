# `save_recent.py`
Saves most recently played tracks to a playlist.

The main use case for me is that I set that playlist to be downloaded offline on my devices. This amounts to forcing Spotify to conduct much more aggressive caching. I find this useful when internet connectivity is unreliable (e.g. on underground trains or planes). As a rough guideline, for downloads on 'very high' quality, 1,000 tracks take up 10 GB.

You can only get the 50 most recent tracks from the API, so you should run this script frequently enough (e.g. every hour).

(This script also saves the recent tracks to a [`shelve`](https://docs.python.org/3/library/shelve.html) shelf for potential future use. Because of Spotify's annoying 50 track limit, there's actually no simple way to get this data again in the future.)