# Scripts
## `save_recent.py`
Saves most recently played tracks to a playlist.

The main use case for me is that I set that playlist to be downloaded offline on my devices. This amounts to forcing Spotify to conduct much more aggressive caching. I find this useful when internet connectivity is unreliable (e.g. on underground trains or planes). As a rough guideline, for downloads on 'very high' quality, 1,000 tracks take up 10 GB.

You can only get the 50 most recent tracks from the API, so you should run this script frequently enough (e.g. every half hour). I do this by deploying to a cloud VPS with Dokku, and scheduling a cron task in Dokku (see `app.json`).


# Deployment
First deployment:
- Define the dokku remote
- `git push dokku`
- Define `ROOT_DIR` as a persistent volume attached to the Dokku container (`dokku storage` on host)
- Define environment variables (`dokku config` on host)

Subsequent deployments:
- `git push dokku`

The Dokku config files are:
- `.buildpacks`
- `app.json`