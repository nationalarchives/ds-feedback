import requests

# from flask import current_app


class ApiResourceNotFound(Exception):
    pass


class BaseAPI:
    api_url = ""
    api_path = "/"
    params = {}

    def __init__(self, api_url):
        self.api_url = api_url

    def add_parameter(self, key, value):
        self.params[key] = value

    def get_results(self, page=None):
        if page:
            self.add_parameter("page", page)
        url = f"{self.api_url}{self.api_path}"
        # current_app.logger.debug(
        #     f"API endpoint requested: {url} (params {self.params})"
        # )
        try:
            response = requests.get(url, params=self.params)
        except ConnectionError:
            # current_app.logger.error(f"API connection error for: {url}")
            raise Exception("A connection error occured with the API")
        if response.status_code == 404:
            # current_app.logger.warning(f"Resource not found: {url}")
            raise ApiResourceNotFound("Resource not found")
        if response.status_code == requests.codes.ok:
            return self.parse_response(response)
        # current_app.logger.error(
        #     f"API responded with {response.status_code} status for {url}"
        # )
        raise ConnectionError("Request to API failed")

    def parse_response(self, response):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            # current_app.logger.error("API provided non-JSON response")
            raise ConnectionError("API provided non-JSON response")
