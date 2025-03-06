#!/usr/bin/env python
import click
import logging
from aiapwn.utils import setup_logger, pretty_format
from aiapwn.recon import ReconManager
from aiapwn.ai_generator import AIPromptGenerator
from aiapwn.scanner import Scanner
from colorama import Fore, Style, init
from aiapwn.playwright_client import PlaywrightClient
import os
import asyncio


# Initialize colorama for cross-platform colored output.
init(autoreset=True)

# Define a simple colored formatter for log messages.
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }
    
    def formatTime(self, record, datefmt=None):
        s = super().formatTime(record, datefmt)
        return f"{Fore.CYAN}{s}{Style.RESET_ALL}"
    
    def format(self, record):
        level_color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def configure_logger():
    # Setup logger using our utility function.
    logger = setup_logger(log_level="INFO", log_file="aiapwn.log")
    # Apply colored formatter to all handlers.
    formatter = ColoredFormatter(
        "[%(asctime)s] [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    return logger

AIAPWN_LOGO = f"""{Fore.YELLOW}       _                    
 ___ _(_)__ ____ _    _____ 
/ _ `/ / _ `/ _ \ |/|/ / _ |  (0.1.0)
\_,_/_/\_,_/ .__/__,__/_//_/
          /_/               {Style.RESET_ALL}
"""

DISCLAIMER = f"""
[!] Disclaimer: This tool is designed for security testing purposes only. Unauthorized use or testing against systems you do not own is illegal and may result in severe penalties. Always ensure you have explicit permission to test a target.

[!] Usage Disclaimer: Use at your own risk. The authors assume no liability for any damage arising from the use of this tool.
"""


@click.command(
    help="""AIAPWN: AI Agent Prompt Injection Testing Tool

Examples of usage:

1. Start testing with GET method:\n
\b
    aiapwn --url http://example.com/chat?query=AIAPWN --method get

2. Start testing with POST method:\n
\b
    aiapwn --url http://example.com/chat/api --method post --req-json '{"prompt":"AIAPWN"}'
"""
)

@click.option("--url", required=True, help="Target AI endpoint URL.")
@click.option("--method", type=click.Choice(["post", "get"]),  help="HTTP method to use (post or get)")
@click.option("--req-json", default=None, help="Raw JSON string for the POST request body, use 'AIAPWN' as placeholder. Example: '{\"prompt\":\"AIAPWN\"}'")
@click.option("--recon-dir", default=None, help="Directory containing recon prompt text files")
@click.option("--payload-dir", default=None, help="Directory containing payload text files")
@click.option("--timeout", default=50, type=int, help="Request timeout in seconds")
@click.option("--evaluate", is_flag=True, help="Enable evaluation of injection attempts")
@click.option("--generate", is_flag=True, help="Enable tailored prompt generation using AI")
@click.option("--num-prompts", default=5, type=int, help="Number of tailored prompts to generate")
def main(url,method, req_json, recon_dir, payload_dir, timeout, evaluate, generate, num_prompts):
        
    if (evaluate or generate) and "OPENAI_API_KEY" not in os.environ:
        raise click.UsageError("OPENAI_API_KEY environment variable must be set for evaluation or generation.")
    
    click.echo(AIAPWN_LOGO)
    click.echo(Fore.CYAN + "aiapwn: AI Agent Prompt Injection Testing Tool" + Style.RESET_ALL)
    click.echo(DISCLAIMER)
    
    logger = configure_logger()
    
    client = PlaywrightClient()
    client.open_url(url)
    
    logger.info("Starting reconnaissance...")


    recon_manager = ReconManager(client=client,endpoint_url=url, recon_dir=recon_dir, timeout=timeout)
    recon_results = recon_manager.run_recon(
        req_json=req_json
    )
    
    logger.info("Generating agent description...")
    description = recon_manager.generate_description()

    logger.info("Agent description: %s", description)

    logger.debug("Agent description generated: %s", description)
    
    # --- Tailored Prompt Generation (Optional) ---
    tailored_prompts = []
    if generate:
        logger.info("Generating tailored injection prompts...")
        generator = AIPromptGenerator()
        generator.generate_prompts(num_prompts=num_prompts)
    else:
        logger.info("Tailored prompt generation not enabled; skipping this step.")
    
    # --- Injection Testing ---
    logger.info("Starting injection testing...")
    scanner = Scanner(
        client=client,
        endpoint_url=url,
        payload_dir=payload_dir,
        timeout=timeout,
    )
    try:
        loop = asyncio.get_running_loop()
        print("An asyncio event loop is already running:", loop)
    except RuntimeError:
        print("No asyncio event loop is running.")

    scanner.run(method=method, req_json=req_json, evaluate=evaluate)
    

if __name__ == '__main__':
    main()
