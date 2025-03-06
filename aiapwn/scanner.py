import logging
from .utils import setup_logger
from .playwright_client import PlaywrightClient
from .payload import PayloadManager
from .ai_evaluator import AIEvaluator
import time, random

logger = logging.getLogger("aiapwn")

class Scanner:
    def __init__(self, client, endpoint_url, payload_dir=None, headers=None, timeout=50, evaluator_model="gpt-4o-mini"):
        """
        Initializes the Scanner with the endpoint URL and optional parameters.

        Args:
            endpoint_url (str): The URL of the AI endpoint.
            payload_dir (str, optional): Directory for loading custom payloads. Defaults to None.
            headers (dict, optional): Headers for the request. Defaults to None.
            timeout (int, optional): Timeout for requests in seconds. Defaults to 50.
        """
        self.client = client if client else PlaywrightClient()
        # self.client.open_url(endpoint_url)
        self.payload_manager = PayloadManager(payload_dir) if payload_dir else PayloadManager()
        self.results = {}
        self.evaluator = AIEvaluator(model=evaluator_model)

    
    def run(self, method="post", req_json='{"prompt":"AIAPWN"}', evaluate=False):
        """
        Executes the scan by iterating through each payload and sending it to the endpoint.

        Args:
            method (str, optional): HTTP method to use ("post" or "get"). Defaults to "post".
            key (str, optional): The key to use in the payload. For POST requests, this is the JSON key;
                                 for GET requests, the query parameter key.

        Returns:
            dict: A dictionary mapping each payload to its corresponding response or error details.
        """
        payloads = self.payload_manager.get_payloads()
        self.results = {}
        for i, payload in enumerate(payloads):
            logger.info("Payload test (%d/%d) '%s' ",  i + 1, len(payloads), payload)
            try:
                response = self.client.auto_detect_response(prompt=payload)
                
                if not isinstance(response, dict):
                    response = {"response": response}

                self.results[payload] = response
                logger.debug("Payload: %s --> Response: %s", payload, response)

                if evaluate and self.evaluator:
                    eval_result = self.evaluator.evaluate_injection(payload, response)
                    self.results[payload]["evaluation"] = eval_result

            except Exception as e:
                self.results[payload] = {"error": str(e)}
                logger.error("Payload: %s --> Error: %s", payload, str(e))

            # Introduce a random delay between requests to avoid overwhelming the server.
            sleep_time = random.uniform(1, 3)
            logger.info("Sleeping for %.2f seconds before the next request...", sleep_time)
            time.sleep(sleep_time)


        return self.results
    


# Basic testing when running this module directly.
if __name__ == '__main__':
    # Replace with a valid endpoint URL for testing.
    test_endpoint = "http://localhost:8000/api/query"
    scanner = Scanner(test_endpoint)
    results = scanner.run(method="post", key="query", evaluate=True)
    
    print("Scan Results:")
    for payload, result in results.items():
        print(f"Payload: {payload}\nResponse: {result}\n")
