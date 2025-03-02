import requests 
import json
from .exceptions import ClientError
import logging
import random
import platform

logger = logging.getLogger("aiapwn")


def extract_all_text_values(data, results=None):
    """
    Recursively collects all string values from a JSON response.
    """
    if results is None:
        results = []

    if isinstance(data, dict):
        for value in data.values():
            extract_all_text_values(value, results)
    elif isinstance(data, list):
        for item in data:
            extract_all_text_values(item, results)
    elif isinstance(data, str) and data.strip():
        results.append(data)
    
    return results


class EndpointClient:
    """
    Handles communication with the target AI endpoint.
    """

    def __init__(self, url, headers=None, timeout=50):
        """
        Initializes the EndpointClient.

        Args:
            url (str): The URL of the AI endpoint.
            headers (dict, optional): Headers to include in the request. Defaults to None.
            timeout (int, optional): Timeout for the request in seconds. Defaults to 10.
        """
        self.url = url
        self.timeout = timeout

        user_agents = [
            f"AIAPWN-Scanner/{random.randint(1, 10)} (Python {platform.python_version()}; {platform.system()})",
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100, 120)}.0.0.0 Safari/537.36",
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 16)}) AppleWebKit/537.36 (KHTML, like Gecko) Version/{random.randint(14, 16)}.0 Safari/537.36",
            f"Mozilla/5.0 (Linux; Android {random.randint(9, 13)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100, 120)}.0.0.0 Mobile Safari/537.36",
        ]

        user_agent = random.choice(user_agents)
        default_headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if headers:
            default_headers.update(headers)

        self.headers = default_headers


    
    def send_post_request(self, payload_value, req_json='{"prompt":"AIAPWN"}'):
        req_json = req_json.replace("AIAPWN", payload_value)

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=json.loads(req_json),
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as req_err:
            raise ClientError(f"POST request failed: {req_err}") from req_err
        try:
            results = extract_all_text_values(response.json())
            return " ".join(results)

        except ValueError as json_err:
            raise ClientError("Failed to parse JSON response from POST : {json_err}") from json_err

    def send_get_request(self, payload_value=None):
        if "AIAPWN" not in self.url:
            raise ClientError("GET request URL must contain 'AIAPWN' placeholder")
        
        params = {self.url.split("AIAPWN")[0]: payload_value}

        
        try:
            response = requests.get(
                self.url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as req_err:
            raise ClientError(f"GET request failed: {req_err}") from req_err

        try:
            results = extract_all_text_values(response.json())
            return " ".join(results)
        except ValueError as json_err:
            raise ClientError("Failed to parse JSON response from GET") from json_err