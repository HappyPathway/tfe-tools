import hcl2
import json
import os
import requests
from glob import glob
from tfe.core import session
from requests import Session

class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

class GitHubRepoDownloader:

    """ class GitHubRepoDownloader """

    def __init__(self, repo, path="/", token=None):
        """
        Initialize a GitHubRepoDownloader instance.
        Args:
        - repo (str): The name of the GitHub repository.
        - path (str): The path within the repository to start downloading files (default: "/").
        - token (str): GitHub personal access token for authentication (optional).
        This constructor initializes the GitHubRepoDownloader object with the provided
        repository name, path, and token. It also fetches the contents of the specified path
        and stores them in the internal file_contents dictionary.
        Note: The _get_files method is automatically called during initialization to populate
        the file_contents dictionary.
        """

        self._repo = repo
        self._base_url = (
            f"https://github.corp.clover.com/api/v3/repos/clover/{self._repo}"
        )
        self._token = token
        self._headers = self._get_headers()
        self._path = path
        self._file_contents = (
            {}
        )  # Initialize an empty dictionary to store file contents
        self._get_files(self._path)

    def _get_headers(self):
        """
        Create and return the headers for the HTTP requests.
        Returns:
        - headers (dict): A dictionary containing request headers.
        This method constructs and returns the headers required for making HTTP requests to
        the GitHub API, including the Authorization header if a token is provided.
        """

        headers = {}
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        return headers

    def _get_contents(self, path):
        """
        Retrieve the contents of a GitHub repository path.
        Args:
        - path (str): The path within the repository.
        Returns:
        - contents (list): A list of dictionaries representing the contents of the path.
        This method sends an HTTP GET request to the GitHub API to retrieve the contents
        of the specified path in the repository. It returns a list of dictionaries where
        each dictionary represents a file or directory in the path.
        """

        url = f"{self._base_url}/contents/{path}"
        response = requests.get(url, headers=self._headers)

        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to retrieve contents from {url}")

    def _get_files(self, path=""):
        """
        Recursively download and store files from a GitHub repository path.
        Args:
        - path (str): The path within the repository (default: "").
        This method recursively downloads and stores files from the specified path and its
        subdirectories in the internal file_contents dictionary. It is called automatically
        during object initialization.
        """
        contents = self._get_contents(path)

        for item in contents:
            if item["type"] == "file":
                file_url = item["download_url"]
                response = requests.get(file_url, headers=self._headers)

                if response.status_code == 200:
                    file_content = response.text
                    file_path = os.path.join(path, item["name"])
                    self._file_contents[
                        file_path
                    ] = file_content  # Store in the internal dictionary
                else:
                    pass  # Handle download failure
            elif item["type"] == "dir":
                subdirectory_path = os.path.join(path, item["name"])
                self._get_files(
                    subdirectory_path
                )  # Recursive call to the internal method

    @property
    def contents(self):
        """
        Get the downloaded file contents.
        Returns:
        - file_contents (dict): A dictionary containing downloaded file contents.
        This property allows access to the file contents that have been downloaded and
        stored in the internal file_contents dictionary.
        """
        return self._file_contents

def get_tfe_session(terraform_url="terraform.corp.clover.com"):
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    url = "https://{0}/api/v2/state-versions".format(terraform_url)
    session.TFESession("https://{0}".format(terraform_url), tkn)
    return session.TFESession

def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)

def get_attr(rsc, attr):
    try:
        attr = [x for x in item_generator(rsc, attr)][0]
        return attr
    except IndexError:
        return None
    
def filter_type(state, rsc_type, managed=True):
    for rsc in state.get('resources'):
        if rsc.get('type') == rsc_type:
            if managed and rsc.get('mode') == 'managed':
                for instance in rsc.get('instances'):
                    yield instance
            else:
                for instance in rsc.get('instances'):
                    yield instance
