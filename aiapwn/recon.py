import os
import glob
import logging
from openai import OpenAI
from .playwright_client import PlaywrightClient
from .exceptions import ClientError
from .config import DEFAULT_RECON_DIR, DEFAULT_REPORT_DIR
import time, random

logger = logging.getLogger("aiapwn")

def load_recon_prompts(recon_dir=DEFAULT_RECON_DIR):
    """
    Loads reconnaissance prompts from all '.txt' files in the specified directory.
    
    Args:
        recon_dir (str): Directory containing recon prompt text files.
    
    Returns:
        list: A list of recon prompts (one per line) loaded from the files.
    """
    prompts = []
    
    if not os.path.isdir(recon_dir):
        logger.warning("Recon directory %s does not exist. Using default hardcoded prompts.", recon_dir)
        return prompts  # Or return a fallback default list if desired.
    
    txt_files = glob.glob(os.path.join(recon_dir, "*.txt"))
    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        prompts.append(line)
        except Exception as e:
            logger.error("Error reading recon file %s: %s", file_path, e)
    return prompts

class ReconManager:
    """
    Manages reconnaissance for the target AI agent by sending preliminary prompts
    (loaded from external files) to gather useful information about its functionality.
    """
    def __init__(self, client, recon_dir=None, report_dir=None):
        """
        Initializes the ReconManager.
        
        """
        self.client = client if client else PlaywrightClient()
        self.recon_dir = recon_dir if recon_dir is not None else DEFAULT_RECON_DIR
        self.report_dir = report_dir if report_dir is not None else DEFAULT_REPORT_DIR
        self.recon_prompts = load_recon_prompts(self.recon_dir)
        self.results = {}

    def run_recon(self):
        """
        Sends each reconnaissance prompt to the endpoint and collects the responses.
        """
        self.results.clear()
        if not self.recon_prompts:
            logger.warning("No recon prompts loaded. Ensure that recon prompt files exist in %s", self.recon_dir)
            return self.results
        
        for i, prompt in enumerate(self.recon_prompts):
            logger.info("Recon Prompt %d/%d: %s", i + 1, len(self.recon_prompts), prompt)
            try:
                response = self.client.auto_detect_response(prompt)
                self.results[prompt] = response
                logger.debug("Recon Prompt: %s --> Response: %s", prompt, response)
            except ClientError as e:
                self.results[prompt] = {"error": str(e)}
                logger.error("Recon Prompt: %s --> Error: %s", prompt, str(e))
            
            sleep_time = random.uniform(1, 5)
            logger.info("Sleeping for %.2f seconds before the next request...", sleep_time)
            time.sleep(sleep_time)
            

        return self.results

    def generate_description(self, model="gpt-4o-mini"):
        """
        Generates a descriptive summary of the AI agent's functionality based on the
        responses gathered during the reconnaissance phase. It queries the OpenAI API
        to summarize the collected responses.

        Args:
            model (str, optional): The model to use for generating the summary. Defaults to "gpt-4o".

        Returns:
            str: A summary description of the AI agent's functionality.
        """
        # Ensure recon has been run.
        if not self.results:
            logger.debug("No recon results available, running recon now...")
            self.run_recon()
        
        # Combine all recon responses into a single string.
        combined_text = ""
        for prompt, response in self.results.items():
            if isinstance(response, dict) and "error" in response:
                combined_text += f"Prompt: {prompt}\nError: {response['error']}\n\n"
            else:
                combined_text += f"Prompt: {prompt}\nResponse: {response}\n\n"
        
        # Construct the summarization prompt for OpenAI.
        summary_prompt = (
            "Based on the following reconnaissance responses from an AI agent, "
            "please provide a concise yet inclusive description of the agent's functionality, "
            "including its capabilities, restrictions, and overall behavior.\n\n"
            f"{combined_text}\n\nSummary:"
        )
        
        # Instantiate the OpenAI client.
        openai = OpenAI()
        
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Give a concise summary of the AI agent's functionality."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0
            )
            summary = response.choices[0].message.content.strip()
            logger.debug("Generated AI Agent Description: %s", summary)
            # Save the summary for reuse.
            self.save_description(summary)
            return summary
        except Exception as e:
            logger.error("Error generating AI agent description: %s", e)
            return f"Error generating description: {e}"

    def save_description(self, description, filename="agent_description.txt"):
        """
        Saves the provided AI agent description to a text file in the recon directory.
        This allows the description to be used later by evaluators or prompt generators,
        or to be manually updated by the user.
        
        Args:
            description (str): The summary description to save.
            filename (str, optional): The name of the file to save the description in.
                                      Defaults to "agent_description.txt".
        """
        file_path = os.path.join(self.report_dir, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(description)
            logger.debug("Description successfully saved to %s", file_path)
        except Exception as e:
            logger.error("Error saving description to file %s: %s", file_path, e)


# Basic testing when running this module directly.
if __name__ == '__main__':
    # Replace with a valid endpoint URL for testing.
    test_endpoint = "http://localhost:3000"
    
    recon_manager = ReconManager(test_endpoint)
    recon_results = recon_manager.run_recon()
    
    print("Recon Results:")
    for prompt, result in recon_results.items():
        print(f"Prompt: {prompt}\nResponse: {result}\n")
    
    description = recon_manager.generate_description()
    print("\nAI Agent Description:")
    print(description)
