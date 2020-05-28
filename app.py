import json
import os
import google_auth_oauthlib.flow as flow
import googleapiclient.discovery as client_discovery
import googleapiclient.errors as errors
import youtube_dl
import requests

spotify_client_id = "Your_spotify_user_name"
spotify_secret = "Your_spotify_token"

class SpotifyPlaylist:
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.song_info = {}

    @staticmethod
    def get_youtube_client():
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        client_file = 'google_secret_json'

        client_flow = flow.InstalledAppFlow.from_client_secrets_file(client_file, scopes)
        credentials = client_flow.run_console()
        client = client_discovery.build("youtube", "v3", credentials=credentials)

        return client

    def get_liked_songs(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",

        )
        response = request.execute()
        print("This is youtube response")
        print(response["items"])
        print("\n")

        for item in response["items"]:

            title = item["snippet"]["title"]
            url = f'https://www.youtube.com/watch?v={item["id"]}'
            song = youtube_dl.YoutubeDL({}).extract_info(url, download=False)
            song_name = song["track"]
            song_artist = song["artist"]
            if song_name is not None and song_artist is not None:
                self.song_info[title] = {
                    "youtube_url": url,
                    "song_name": song_name.lower(),
                    "artist": song_artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.spotify_uri(song_name, song_artist)

                }
            else:
                continue

    def spotify_uri(self, song_name, song_artist):
        try:
            query = f'https://api.spotify.com/v1/search/?q=track%3A{song_name}+artist%3A{song_artist}&type=track&offset=0&limit=20'
            response = requests.get(
                query,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {spotify_secret}"
                }
            )
            json_res = response.json()
            print(json_res)
            print("\n")
            songs = json_res["tracks"]["items"]


            print("These are the songs")
            print(len(songs))

            return songs[0]["uri"]
        except Exception:
            pass

    def create_spotify_playlist(self):
        """
        This is where all this comes down to. We're about to create spotify playlist
        """

        request_body = json.dumps({
            "name": "Youtube Liked Songs",
            "description": "playlist of the songs which I liked on youtube",
            "public": False,
            "collaborative": False
        })
        query = f'https://api.spotify.com/v1/users/{spotify_client_id}/playlists'
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_secret}"

            }

        )
        json_res = response.json()

        return json_res["id"]

    def add_songs(self):
        try:
            self.get_liked_songs()

            uris = [info["spotify_uri"] for song, info in self.song_info.items()]
            id = self.create_spotify_playlist()

            req_data = json.dumps(uris)
            query = f'https://api.spotify.com/v1/playlists/{id}/tracks'
            response = requests.post(
                query,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {spotify_secret}"

                }

            )
            if response.status_code != 201:
                raise Exception(f"Error occurred {response.json()} \n Error Code {response.status_code}")

            json_res = response.json()
            return json_res
        except Exception:
            pass


if __name__ == "__main__":
    spotify_playlist = SpotifyPlaylist()
    spotify_playlist.add_songs()
