import time 
import logging
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError
from .utils import setup_logger



logger = setup_logger(log_level="INFO", log_file="aiapwn.log")
logger = logging.getLogger("aiapwn")


class PlaywrightClient:
    def __init__(self, headless: bool = False) -> None:
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        self.input_field_index = None
        self.submit_button_index = None
        self.baseline = ""
        logger.info("Initialized Playwright with headless=%s", headless)


    def open_url(self, url: str) -> None:
        """Opens the specified URL in the browser and waits until the page is fully loaded."""
        logger.info("Navigating to URL: %s", url)
        # Navigate and wait until the network is idle (i.e. no network connections for at least 500 ms)
        # self.page.goto(url, wait_until="networkidle")
        
        # Alternatively, you could call wait_for_load_state if needed:
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")
        
        self.baseline = self.page.locator("body").inner_text().strip()
        logger.info("Initial baseline text captured.")


    def auto_detect_input_fields(self) -> List[str]:
        candidates = []
        locator = self.page.locator("input, textarea, [contenteditable='true']")
        count = locator.count()
        for i in range(count):
            element = locator.nth(i)
            outer_html = element.evaluate("el => el.outerHTML")
            candidates.append(outer_html)
        if not candidates:
            logger.error("No input fields detected automatically.")
        else:
            logger.info("Detected %d input fields.", len(candidates))
        return candidates
    
    def auto_detect_submit_buttons(self) -> List[str]:
        """Automatically detects submit buttons on the page."""
        logger.info("Attempting to detect submit buttons...")
        candidates = []
        # Look for buttons and input[type="submit"]
        locator = self.page.locator("button, input[type='submit']")
        count = locator.count()
        
        for i in range(count):
            element = locator.nth(i)
            outer_html = element.evaluate("el => el.outerHTML")
            candidates.append(outer_html)
            
        if not candidates:
            logger.error("No submit buttons detected automatically.")
        else:
            logger.info("Detected %d submit buttons.", len(candidates))
            
        return candidates
    
    def choose_submit_button(self) -> Optional[int]:
        """Allows the user to choose a submit button from detected candidates.
        
        Returns:
            Optional[int]: The index of the chosen submit button, or None if no valid choice was made.
        """
        if self.submit_button_index is not None:
            logger.info("Using previously selected submit button index: %s", self.submit_button_index)
            return self.submit_button_index

        candidates = self.auto_detect_submit_buttons()
        if not candidates:
            return None

        print("Detected submit buttons:")
        for i, button in enumerate(candidates):
            print(f"{i}: {button}")

        choice = input("Enter the index of the submit button to use: ")

        try:
            choice_int = int(choice)
            if 0 <= choice_int < len(candidates):
                self.submit_button_index = choice_int  # Store the chosen index for future use.
                return choice_int
            else:
                print("Invalid choice. Please enter a valid index.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        return None


    def choose_input_field(self) -> Optional[int]:
        if self.input_field_index is not None:
            logger.info("Using previously selected input field index: %s", self.input_field_index)
            return self.input_field_index

        candidates = self.auto_detect_input_fields()
        if not candidates:
            return None

        print("Detected input fields:")
        for i, field in enumerate(candidates):
            print(f"{i}: {field}")

        choice = input("Enter the index of the input field to use: ")

        try:
            choice_int = int(choice)
            if 0 <= choice_int < len(candidates):
                self.input_field_index = choice_int  # Store the chosen index for future use.
                return choice_int
            else:
                print("Invalid choice. Please enter a valid index.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        return None
    
    def send_prompt(self, prompt: str) -> None:
        logger.debug("Sending prompt: %s", prompt)

        selected_index = self.choose_input_field()
        if selected_index is None:
            logger.error("No valid input field selected.")
            return
        
        submit_index = self.choose_submit_button()
        if submit_index is None:
            logger.warning("No valid submit button selected. Will try to use Enter key instead.")
        
        # Handle input field
        input_locator = self.page.locator("input, textarea, [contenteditable='true']")
        input_element = input_locator.nth(selected_index)
        input_element.fill("")
        input_element.fill(prompt)
        
        # Handle submit button if available, otherwise use Enter key
        if submit_index is not None:
            submit_locator = self.page.locator("button, input[type='submit']")
            submit_element = submit_locator.nth(submit_index)
            submit_element.click()
        else:
            self.page.keyboard.press("Enter")
            
        logger.info("Prompt sent successfully.")
    
    def update_baseline(self) -> None:
        self.baseline = self.page.locator("body").inner_text().strip()
        logger.info("Baseline updated.")


    def auto_detect_response(self, prompt:str, timeout:int = 60000, stability_duration:int = 6000) -> str:
        """
        Sends a test prompt and uses a MutationObserver to detect new content in the response container.
        Returns a string containing the concatenated text of newly added nodes.
        
        Args:
            prompt: The text to send as a prompt
            timeout: Maximum time (ms) to wait for a response
            stability_duration: Time (ms) to wait with no changes before considering response complete
        
        This helps you see which parts of the DOM change in response to a prompt so you can adjust
        the baseline selector if necessary.
        """
        logger.debug("Sending test prompt for auto-detection of response fields: %s", prompt)
        # Send the test prompt. (This will prompt the user to choose an input field if needed.)
        self.send_prompt(prompt)
        self.page.wait_for_load_state("domcontentloaded")
        logger.debug("Waiting for response...")
        # Inject a MutationObserver into the page context to capture added text.
        script = f"""
        () => {{
            return new Promise((resolve, reject) => {{
                const target = document.querySelector('body');
                if (!target) {{
                    reject("Response container (body) not found.");
                    return;
                }}
                let addedText = "";
                let lastChangeTime = Date.now();
                let stabilityTimer = null;
                
                const observer = new MutationObserver((mutations, obs) => {{
                    let hasNewContent = false;
                    mutations.forEach(mutation => {{
                        mutation.addedNodes.forEach(node => {{
                            if (node.nodeType === Node.TEXT_NODE) {{
                                addedText += node.textContent;
                                hasNewContent = true;
                            }} else if (node.nodeType === Node.ELEMENT_NODE) {{
                                addedText += node.innerText;
                                hasNewContent = true;
                            }}
                        }});
                    }});
                    
                    // If we have new content, update the last change time
                    if (hasNewContent) {{
                        lastChangeTime = Date.now();
                        // Clear any existing stability timer
                        if (stabilityTimer) {{
                            clearTimeout(stabilityTimer);
                            stabilityTimer = null;
                        }}
                        
                        // Set a new stability timer to check if content has stopped changing
                        stabilityTimer = setTimeout(() => {{
                            // If no changes for stability_duration ms, consider it complete
                            if (Date.now() - lastChangeTime >= {stability_duration}) {{
                                obs.disconnect();
                                resolve(addedText.trim());
                            }}
                        }}, {stability_duration});
                    }}
                }});
                
                observer.observe(target, {{ childList: true, subtree: true, characterData: true }});
                
                // Fallback: after timeout milliseconds, disconnect and resolve with what we've gathered.
                setTimeout(() => {{
                    observer.disconnect();
                    if (stabilityTimer) {{
                        clearTimeout(stabilityTimer);
                    }}
                    resolve(addedText.trim());
                }}, {timeout});
            }});
        }}
        """
        response_text = self.page.evaluate(script)
        logger.debug("MutationObserver detected added text: %s", response_text)
        self.update_baseline()
        return response_text




def main():
    client = PlaywrightClient(headless=False)
    client.open_url("http://localhost:3000")

    PROMPTS = [
        "What is the capital of France?",
        "Tell me a joke.",
        "What is the meaning of life?"
    ]
    for prompt in PROMPTS:
        res = client.auto_detect_response(prompt)

        logger.info("Prompt: %s",prompt)
        logger.info("Response: %s",res)

if __name__ == "__main__":
    main()