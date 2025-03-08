import logging
from .utils import setup_logger
from .playwright_client import PlaywrightClient
from .payload import PayloadManager
from .ai_evaluator import AIEvaluator
import time, random

logger = logging.getLogger("aiapwn")

class Scanner:
    def __init__(self, client, payload_dir=None, evaluator_model="gpt-4o-mini"):
        """
        Initializes the Scanner with the endpoint URL and optional parameters.
        """
        self.client = client if client else PlaywrightClient()
        self.payload_manager = PayloadManager(payload_dir) if payload_dir else PayloadManager()
        self.results = {}
        self.evaluator = AIEvaluator(model=evaluator_model)

    
    def run(self, evaluate=False):
        """
        Executes the scan by iterating through each payload and sending it to the endpoint.
        """
        payloads = self.payload_manager.get_payloads()
        self.results = {}
        for i, payload in enumerate(payloads):
            logger.info("Payload test (%d/%d)",  i + 1, len(payloads))
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
    