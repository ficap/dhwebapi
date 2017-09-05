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
    def __init__(self, username=None, password=None, token=None):
        # type: (str or None, str or None, str or None) -> DockerHubWebAPI
        """
        Instance can be made by a combination of username and password or using a valid token.
        If you use just a token remember that a new one should be obtained only by
        using self.login(username, password)
        """
        self.token = token
        self.username = username
        self.password = password

        if not self.token and self.username is not None and self.password is not None:
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
        """
        It uses self.username and self.password by default
        These two can be overwritten by username, password
        It provides an option to swap the user without need of making a new instance
        """
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
    from argparse import ArgumentParser, FileType

    def requires_login(argss):
        token = None
        tokenfile = None
        try:
            token = argss.token
        except AttributeError:
            pass

        try:
            tokenfile = argss.tokenfile
        except AttributeError:
            pass

        if token is not None:
            dhapi = DockerHubWebAPI(token=argss.token)

        elif tokenfile is not None:
            dhapi = DockerHubWebAPI(token=argss.tokenfile.readline().rstrip())
            argss.tokenfile.close()
        else:
            username = argss.username or input("Username: ")
            password = argss.password or getpass("Password: ")

            dhapi = DockerHubWebAPI(username, password)

        return dhapi

    def requires_input(argss):
        if argss.file is not None:
            file = argss.file
            inp = "".join(file.readlines())
            file.close()
        else:
            inp = sys.stdin.read()

        return inp

    def update_repo_full_description(argss):
        dhwebapi = requires_login(argss)
        content = requires_input(argss)
        dhwebapi.set_repository_full_description(argss.namespace, argss.repository, content)

    def update_repo_description(argss):
        dhwebapi = requires_login(argss)
        content = requires_input(argss)
        dhwebapi.set_repository_short_description(argss.namespace, argss.repository, content)

    def get_token(argss):
        dhwebapi = requires_login(argss)
        print(dhwebapi.token)

    usage = '''
    usage: dhwebapi command [opt_args] [mandatory_args]
    
    commands:
        update-repo-full-description
            optional args:
                -u, --username USERNAME
                -p, --password PASSWORD
                    NOT RECOMMENDED 
                -t, --token TOKEN
                --tokenfile TOKENFILE
                -f, --file FILE
            
            mandatory args:
                NAMESPACE
                REPOSITORY
        
        update-repo-description
            optional args:
                -u, --username USERNAME
                -p, --password PASSWORD
                    NOT RECOMMENDED 
                -t, --token TOKEN
                --tokenfile TOKENFILE
                -f, --file FILE
            
            mandatory args:
                NAMESPACE
                REPOSITORY
                
        get-token
            optional args:
                -u, --username USERNAME
                -p, --password PASSWORD
                    NOT RECOMMENDED 
    '''

    arg_parser = ArgumentParser(prog="dhwebapi", usage=usage)

    subparsers = arg_parser.add_subparsers()
    subcmds = dict()

    subcmds["update-repo-full-description"] = subparsers.add_parser("update-repo-full-description")
    subcmds["update-repo-description"] = subparsers.add_parser("update-repo-description")

    subcmds["update-repo-full-description"].set_defaults(func=update_repo_full_description)
    subcmds["update-repo-description"].set_defaults(func=update_repo_description)

    for subcmd in subcmds.values():
        subcmd.add_argument("namespace")
        subcmd.add_argument("repository")
        subcmd.add_argument("-u", "--username",
                            help="Use this username for identification during communication with hub.docker.com",
                            required=False)
        subcmd.add_argument("-p", "--password",
                            help="Use this password for identification during communication with hub.docker.com \n "
                                 "THIS IS NOT RECOMMENDED BECAUSE PASSWORD MAY BE SHOWN IN COMMANDS LOG!",
                            required=False)
        subcmd.add_argument("-f", "--file",
                            help="Use this file as an input for pushing operations",
                            required=False, type=FileType())
        subcmd.add_argument("-t", "--token",
                            help="Use this token as identification during communication with hub.docker.com",
                            required=False)
        subcmd.add_argument("--tokenfile",
                            help="Use token in this file for authentication during communication.",
                            required=False, type=FileType())

    subcmds["get-token"] = subparsers.add_parser("get-token")
    subcmd = subcmds["get-token"]
    subcmd.set_defaults(func=get_token)
    subcmd.add_argument("-u", "--username",
                        help="Use this username for identification during communication with hub.docker.com",
                        required=False)
    subcmd.add_argument("-p", "--password",
                        help="Use this password for identification during communication with hub.docker.com \n "
                             "THIS IS NOT RECOMMENDED BECAUSE PASSWORD MAY BE SHOWN IN COMMANDS LOG!",
                        required=False)

    # subcmd.add_argument("--tokenfile",
    #                     help="Write obtained token to this file. REPLACES EXISTING CONTENT IN FILE IF ANY!",
    #                     required=False, type=FileType(mode='w'))

    args = arg_parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        arg_parser.print_help()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(_main())
