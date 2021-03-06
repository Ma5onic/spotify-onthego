from __future__ import print_function
from __future__ import unicode_literals

import json
import os

import appdirs
import spotipy
import spotipy.util


# Python 3-compatible user input
try:
    input = raw_input
except NameError:
    pass


class TokenDispenser(object):

    def __init__(self):
        self._token = None
        self._credentials = None

    @property
    def spotify_token(self):
        if self._token is None:
            token = self.load_token()
            if token is None or not self.is_token_valid(token):
                token = self.get_new_token()
                self.save_token(token)
            self._token = token
        return self._token

    def load_token(self):
        token_path = self.get_token_path()
        if not os.path.exists(token_path):
            return None
        with open(token_path) as token_file:
            return token_file.read().strip()

    def get_new_token(self):
        token = spotipy.util.prompt_for_user_token(
            self.spotify_username,
            client_id=self.spotify_client_id,
            client_secret=self.spotify_client_secret,
            redirect_uri=self.spotify_redirect_uri,
            scope="playlist-read-private user-library-read"
        )
        return token

    def is_token_valid(self, token):
        try:
            spotify_client = spotipy.Spotify(auth=token)
            spotify_client.current_user()
        except spotipy.client.SpotifyException:
            return False
        return True

    def save_token(self, token):
        token_path = self.get_token_path()
        self.check_directory_exists(token_path)
        with open(token_path, "w") as token_file:
            token_file.write(token)

    @property
    def credentials(self):
        if self._credentials is None:
            try:
                credentials = self.load_credentials()
            except CredentialsNotFound as e:
                credentials = self.ask_for_credentials(**e.credentials_found)
                self.save_credentials(*credentials)
            self._credentials = credentials
        return self._credentials

    @property
    def spotify_username(self):
        return self.credentials[0]
    @property
    def spotify_client_id(self):
        return self.credentials[1]
    @property
    def spotify_client_secret(self):
        return self.credentials[2]
    @property
    def spotify_redirect_uri(self):
        return self.credentials[3]
    @property
    def google_developer_key(self):
        return self.credentials[4]

    def load_credentials(self):
        credentials_path = self.get_credentials_path()
        if not os.path.exists(credentials_path):
            raise CredentialsNotFound("Credentials file not found or not readable")
        credentials = {}
        try:
            with open(credentials_path) as credentials_file:
                credentials = json.load(credentials_file)
            return (
                credentials["USERNAME"],
                credentials["CLIENT_ID"],
                credentials["CLIENT_SECRET"],
                credentials["REDIRECT_URI"],
                credentials["GOOGLE_DEVELOPER_KEY"]
            )
        except (ValueError, KeyError):
            raise CredentialsNotFound("Could not parse credentials file", **credentials)

    def ask_for_credentials(self, **credentials_found):
        print("""You need to register as a developer and create a Spotify app in order to use spotify-onthego.
You may create an app here: https://developer.spotify.com/my-applications/#!/applications/create
You also need to register a youtube app developer key. The app key can be
obtained for free here: https://console.cloud.google.com/apis/api/youtube/overview
Please enter your app credentials:""")
        username = credentials_found.get("USERNAME") or input("Spotify username: ")
        client_id = credentials_found.get("CLIENT_ID") or input("Spotify client ID: ")
        client_secret = credentials_found.get("CLIENT_SECRET") or input("Spotify client secret: ")
        redirect_uri = credentials_found.get("REDIRECT_URI") or input("Spotify redirect URI: ")
        google_developer_key = credentials_found.get("GOOGLE_DEVELOPER_KEY") or input("Google developer key: ")
        return username, client_id, client_secret, redirect_uri, google_developer_key

    def save_credentials(self, username, client_id, client_secret, redirect_uri, google_developer_key):
        credentials_path = self.get_credentials_path()
        print("Saving Spotify credentials to", credentials_path)
        self.check_directory_exists(credentials_path)
        with open(credentials_path, "w") as credentials_file:
            json.dump({
                "USERNAME": username,
                "CLIENT_ID": client_id,
                "CLIENT_SECRET": client_secret,
                "REDIRECT_URI": redirect_uri,
                "GOOGLE_DEVELOPER_KEY": google_developer_key,
            }, credentials_file)

    def get_token_path(self):
        return self.get_config_file_path("spotify.token")

    def get_credentials_path(self):
        return self.get_config_file_path("credentials.json")

    def get_config_file_path(self, filename):
        # We used to store config files in ~/.local, so we still need to
        # support config files stored there
        config_dir = os.path.expanduser("~/.local/share/spotify-onthego/")

        # This is the more modern way of storing config files (cross-platform)
        if not os.path.exists(config_dir):
            config_dir = appdirs.user_config_dir("spotify-onthego")

        return os.path.join(config_dir, filename)

    def check_directory_exists(self, path):
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)


class CredentialsNotFound(Exception):
    def __init__(self, message, **credentials_found):
        super(CredentialsNotFound, self).__init__(message)
        self.credentials_found = credentials_found
