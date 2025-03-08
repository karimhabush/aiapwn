# aiapwn
# AIAPWN - AI Agent Prompt Injection Testing Tool

AIAPWN is a simple tool for testing AI agents against prompt injection vulnerabilities.

## Features

- Recon to understand agent capabilities
- Payload testing with enabled prompts
- Evaluation of injection attempts using GenAI
- Generation of tailored injection prompts

## Installation
### Prerequisites

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Using Poetry

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aiapwn.git
   cd aiapwn
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

### Environment Setup

For evaluation and AI prompt generation features, you'll need an OpenAI API key:

1. Create a `.env` file in the project root:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

2. Or set the environment variable directly:
   ```bash
   export OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Basic Usage

Run the tool with the following command:

```bash
python3 -m aiapwn --url <target-url> [options]
```

### Examples 

Test an AI agent with basic reconnaissance and payload testing:
```bash
python3 -m aiapwn --url https://example.com/ai-chatbot
```

Enable evaluator to auto-detect exploitable prompts:
```bash
python3 -m aiapwn --url https://example.com/ai-chatbot --evaluate
```

Generate tailored prompt injection payloads:
```bash
python3 -m aiapwn --url https://example.com/ai-chatbot --generate --num-prompts 10
```

Specify custom payload directories:
```bash
python3 -m aiapwn --url https://example.com/ai-chatbot --payload-dir /path/to/payloads --recon-dir /path/to/recon
```

## Disclaimer

This tool is designed for security testing purposes only. Unauthorized use or testing against systems you do not own is illegal and may result in severe penalties. Always ensure you have explicit permission to test a target.


## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
