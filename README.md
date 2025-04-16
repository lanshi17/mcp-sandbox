# Python MCP Sandbox

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/release/python-3120/)

Python MCP Sandbox is an interactive Python code execution environment that allows users and llms to safely execute Python code and install packages in isolated Docker containers.

## Features

- 🐳 **Docker Isolation**: Securely run Python code in isolated Docker containers
- 📦 **Package Management**: Easily install and manage Python packages
- 📊 **File Generation**: Support for generating files and accessing them via web links
- 🔄 **Automatic Cleanup**: Containers and generated files are automatically cleaned up after a period of inactivity

## Installation

```bash
# Clone the repository
git clone https://github.com/JohanLi233/python-mcp-sandbox.git
cd python-mcp-sandbox

uv venv

# Start the server
uv run mcp_sandbox.py
```

The server will run at http://localhost:8000, and you can interact with it via the MCP Inspector through SSE.

### Available Tools

1. **Create Python Environment**: Creates a new Docker container for Python execution and returns its ID
2. **Execute Python Code**: Executes Python code in a specified Docker container
3. **Install Python Package**: Installs Python packages in a specified Docker container

## Project Structure

```
python-mcp-sandbox/
├── mcp_sandbox.py     # Main application file
├── Dockerfile         # Docker configuration for Python containers
├── results/           # Directory for generated files
└── README.md          # Project documentation
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 