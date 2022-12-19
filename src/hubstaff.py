import configparser
import logging
import os

import requests

DEFAULT_CONF_PATH = os.path.join(os.path.realpath(os.path.dirname(__file__)), "data/hs_conf")

REQUIRED_VALUES = {
    "email",
    "password",
    "app_token",
    "base_url",
    "api_version",
    "org_name",
}


class ConfigurationError(BaseException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ApiError(BaseException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HubstaffClient:

    """
    .##..##..##..##..#####....####...######...####...######..######...........####...##......######..######..##..##..######.
    .##..##..##..##..##..##..##........##....##..##..##......##..............##..##..##........##....##......###.##....##...
    .######..##..##..#####....####.....##....######..####....####............##......##........##....####....##.###....##...
    .##..##..##..##..##..##......##....##....##..##..##......##..............##..##..##........##....##......##..##....##...
    .##..##...####...#####....####.....##....##..##..##......##...............####...######..######..######..##..##....##...
    ........................................................................................................................
    """

    def __init__(self, conf_path=None, logging_level=logging.WARNING):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)

        self.config = None
        self.conf_path = None
        self.page_limit = 500  # max

        if conf_path is None:
            self.logger.info(
                f"No path to configuration file provided. Using default location: {DEFAULT_CONF_PATH}"
            )
            conf_path = DEFAULT_CONF_PATH
        if os.path.exists(conf_path):
            self.conf_path = conf_path
        else:
            raise ConfigurationError(
                f"{conf_path} does not exist. Cannot load credentials via configuration file."
            )

        self._load_config()
        self.api_url = f"{self.config['base_url']}/{self.config['api_version']}"
        self.session = requests.Session()
        self.session.params.update(
            {
                "app_token": self.config["app_token"]
            }
        )
        self.generate_auth_token()

    def _make_api_call(self, method, path, **kwargs):
        kwargs.update({
            "timeout": 10  # default timeout
        })
        resp = method(f"{self.api_url}/{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _load_config(self):
        config = configparser.ConfigParser()
        config.read(self.conf_path)
        self.config = config["DEFAULT"]
        missing_fields = REQUIRED_VALUES - set(self.config.keys())
        if missing_fields:
            raise ConfigurationError(
                f'Config file missing following values: {", ".join(missing_fields)}'
            )
        self.logger.info("Configuration file successfully loaded.")

    def generate_auth_token(self):
        self.logger.info("generating auth token")
        data = {"email": self.config["email"], "password": self.config["password"]}
        resp = self.session.post(f"{self.api_url}/user/login", data=data)
        resp.raise_for_status()
        auth_token = resp.json()["auth_token"]
        self.session.headers.update(
            {
                "AuthToken": auth_token
            }
        )
        self.logger.info("token generated")
        return auth_token

    def paginate(self, *, page_token=None, **kwargs):
        if page_token:
            params = kwargs.get("params", {})
            params["page_start_id"] = page_token
        data = self._make_api_call(**kwargs)
        page_token = data.get("pagination", {}).get("next_page_start_id")
        yield data
        if page_token:
            yield from self.paginate(page_token=page_token, **kwargs)


class HubstaffOrgClient(HubstaffClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.org_id = self.get_org_id_by_name(self.config["org_name"])

    def get_org_id_by_name(self, name):
        data = self._make_api_call(self.session.get, "groups")
        orgs = data["organizations"]
        for org in orgs:
            if org["name"] == name:
                return org["id"]
        raise ConfigurationError(f"Organization {name} was not found")

    def get_projects(self):
        params = {"page_limit": self.page_limit}
        yield from self.paginate(
            method=self.session.get,
            path=f"groups/{self.org_id}/tasks",
            params=params
        )

    def get_project_activity(self, project_id, start, end, additional_headers=None, additional_params=None):
        headers = {"DateStart": start, "DateStop": end}
        if additional_headers:
            headers.update(additional_headers)
        params = {"page_limit": self.page_limit}
        if additional_params:
            params.update(additional_params)
        yield from self.paginate(
            method=self.session.get,
            path=f"tasks/{project_id}/actions/day",
            headers=headers,
            params=params,
        )
