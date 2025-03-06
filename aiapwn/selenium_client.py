import time
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service  # Modern way to set driver path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import DEFAULT_CHROME_DRIVER_PATH  # e.g. "/usr/bin/chromedriver"

logger = logging.getLogger("aiapwn")


class SeleniumClient:
    """
    A client for automating interactions with a web-based AI agent using Selenium with XPath selectors.
    
    Attributes:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
    """
    def __init__(self, driver_path: str = DEFAULT_CHROME_DRIVER_PATH, headless: bool = False) -> None:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        service = Service(driver_path)
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Initialized Selenium WebDriver with headless=%s", headless)
        except Exception as e:
            logger.error("Error initializing WebDriver: %s", e)
            raise

    def open_url(self, url: str) -> None:
        """Opens the specified URL in the browser."""
        logger.info("Navigating to URL: %s", url)
        self.driver.get(url)

    def send_prompt(self, prompt: str, input_xpath: str, submit_xpath: Optional[str] = None) -> None:
        """
        Sends a prompt to the input field identified by the given XPath, then submits it.
        
        Args:
            prompt (str): The prompt text to send.
            input_xpath (str): XPath for the input field.
            submit_xpath (Optional[str]): XPath for the submit button (if any).
        """
        logger.info("Sending prompt: %s", prompt)
        try:
            input_element = self.driver.find_element(By.XPATH, input_xpath)
            input_element.clear()
            input_element.send_keys(prompt)
            if submit_xpath:
                submit_element = self.driver.find_element(By.XPATH, submit_xpath)
                submit_element.click()
            else:
                input_element.send_keys(Keys.ENTER)
        except Exception as e:
            logger.error("Error sending prompt '%s': %s", prompt, e)
            raise

    def get_response_text(self, response_xpath: str, timeout: int = 10) -> str:
        """
        Retrieves the text from the element that contains the AI response using XPath.
        
        Args:
            response_xpath (str): XPath for the response element.
            timeout (int): Maximum time to wait for the response element.
        
        Returns:
            str: The text content of the response element.
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            response_element = wait.until(EC.visibility_of_element_located((By.XPATH, response_xpath)))
            response_text = response_element.text
            logger.info("Received response: %s", response_text)
            return response_text
        except Exception as e:
            logger.error("Error retrieving response using XPath '%s': %s", response_xpath, e)
            raise

    def close(self) -> None:
        """Closes the browser session."""
        logger.info("Closing the browser.")
        self.driver.quit()


def main():
    """
    Demonstrates how to use SeleniumClient to automate a web-based AI chat interface using XPath selectors.
    
    Update the URL and XPath expressions to match your target site's structure.
    """
    # Initialize the Selenium client (set headless=True to run without a visible browser)
    client = SeleniumClient(headless=False)

    # 1. Open the desired URL (e.g., your web-based AI agent)
    test_url = "http://localhost:3000"
    client.open_url(test_url)

    # 2. Send a prompt (update XPath selectors as needed)
    prompt_text = "Hello, can you tell me more about your capabilities?"
    input_xpath = "//*[@name='message']"       # XPath for the input field
    submit_xpath = "//*[@type='submit']"     # XPath for the submit button (optional)
    client.send_prompt(prompt_text, input_xpath, submit_xpath)

    # 3. Wait for the response to appear (or use explicit waits as needed)
    time.sleep(2)

    # 4. Retrieve the response (update the XPath as needed)
    response_xpath = "//div/p"
    response_text = client.get_response_text(response_xpath)
    print("AI Response:", response_text)

    # 5. Close the browser when done
    client.close()


if __name__ == "__main__":
    main()
