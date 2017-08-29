#!/usr/bin/env python3
"""Python library for easy communication with hub.docker.com

It uses undocumented API which is primarily used by hub.docker.com frontend
for gathering content into its site templates.
"""

from requests import request, Response
from getpass import getpass

ADDRESS_PREFIX = "https://hub.docker.com"
API_VER = "v2"


class DockerHubWebAPI:
    def __init__(self, username, password, token=None):
        # type: (str, str, str or None) -> DockerHubWebAPI
        """
        Instance can be made by a combination of username and password or using a valid token.
        If you use just a token remember that a new one should be obtained only by
        using self.login(username, password)
        """
        self.token = token
        self.username = username
        self.password = password

        if not self.token:
            self.login()

    def _send_request(self, method, command, data=None):
        return request(method,
                       "/".join([ADDRESS_PREFIX, API_VER, command, ""]),  # address MUST end with / so last is "" !!!

                       headers={"Authorization": "JWT " + self.token}
                       if self.token is not None and command != "users/login" else None,

                       json=data
                       )

    @staticmethod
    def _handle_response(response):
        # type: (Response) -> None

        if response.status_code != 200:
            raise DockerHubException(response.status_code, response.url, response.headers, response.content)

    def login(self, username=None, password=None):
        if username is not None and password is not None:
            self.username = username
            self.password = password

        r = self._send_request("POST", "/".join(["users", "login"]),
                               data={"username": self.username, "password": self.password})

        self._handle_response(r)
        if "token" not in r.json():
            raise DockerHubException(r.status_code, r.url, r.headers, r.json())

        self.token = r.json()["token"]

    @property
    def is_logged_in(self):
        if self.token is None:
            return False

        return True

    def get_repository_info(self, namespace, repo_name):
        r = self._send_request("GET", "/".join(["repositories", namespace, repo_name]))
        self._handle_response(r)
        return r.json()

    def set_repository_full_description(self, namespace, repo_name, full_description):
        r = self._send_request("PATCH", "/".join(["repositories", namespace, repo_name]),
                               data={"full_description": full_description})
        self._handle_response(r)

    def set_repository_short_description(self, namespace, repo_name, short_description):
        r = self._send_request("PATCH", "/".join(["repositories", namespace, repo_name]),
                               data={"description": short_description})
        self._handle_response(r)


class DockerHubException(Exception):
    def __init__(self, status_code, url, headers, data):
        self.status_code = status_code
        self.url = url
        self.headers = headers
        self.data = data

    def __str__(self):
        return "status code: " + str(self.status_code) \
               + "\n url: " + self.url \
               + "\n headers: " + str(self.headers) \
               + "\n response: " + str(self.data)


def _main():
    requires_login = ["update-repo-full-description", "update-repo-description"]
    requires_input = ["update-repo-full-description", "update-repo-description"]

    from argparse import ArgumentParser, FileType
    arg_parser = ArgumentParser(prog="dhwebapi")
    arg_parser.add_argument("-u", "--username",
                            help="Use this username for identification during communication with hub.docker.com",
                            required=False)
    arg_parser.add_argument("-p", "--password",
                            help="Use this password for identification during communication with hub.docker.com \n "
                                 "THIS IS NOT RECOMMENDED BECAUSE PASSWORD MAY BE SHOWN IN COMMANDS LOG!",
                            required=False)
    arg_parser.add_argument("-f", "--file",
                            help="Use this file as an input for pushing operations",
                            required=False, type=FileType())
    arg_parser.add_argument("-t", "--token",
                            help="Use this token as identification during communication with hub.docker.com",
                            required=False)
    arg_parser.add_argument("--tokenfile",
                            help="Use token in this file for authentication during communication.",
                            required=False, type=FileType())
    arg_parser.add_argument("command", choices=["update-repo-full-description", "update-repo-description"])
    arg_parser.add_argument("namespace")
    arg_parser.add_argument("repo")
    args = arg_parser.parse_args()

    if args.command in requires_login:
        if args.token is not None:
            dhapi = DockerHubWebAPI(username="", password="", token=args.token)

        elif args.tokenfile is not None:
            # noinspection PyBroadException
            dhapi = DockerHubWebAPI(username="", password="", token=args.tokenfile.readline().rstrip())
            args.tokenfile.close()
        else:
            username = args.username or input("Username: ")
            password = args.password or getpass("Password: ")

            dhapi = DockerHubWebAPI(username, password)
    else:
        dhapi = DockerHubWebAPI("", "", "")

    inp = ""
    if args.command in requires_input:
        if args.file is not None:
            file = args.file
            inp = "".join(file.readlines())
            file.close()
        else:
            inp = sys.stdin.read()

    # currently there are only two supported commands
    if args.command == "update-repo-full-description":
        dhapi.set_repository_full_description(args.namespace, args.repo, inp)
    elif args.command == "update-repo-description":
        dhapi.set_repository_short_description(args.namespace, args.repo, inp)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(_main())
