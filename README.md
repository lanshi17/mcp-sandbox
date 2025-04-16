# Python MCP Sandbox

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

The default SSE endpoint is http://localhost:8000/sse, and you can interact with it via the MCP Inspector through SSE or any other client that supports SSE connections.

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

## Example Prompt
```
I've configured a Python code execution environment for you. You can run Python code using the following steps:

1. First, use the "Create Python virtual environment" tool to create a virtual environment
   - This will return an environment ID which you'll need for subsequent operations

2. If you need to install packages, use the "Install Python package" tool
   - Parameters: env_id (environment ID) and package_name (e.g., numpy, pandas)
   - Example: Install numpy and matplotlib

3. Use the "Execute Python code" tool to run your code
   - Parameters: env_id (environment ID) and code (Python code)
   - You can write any Python code including data processing, visualization, file operations, etc.

Example workflow:
- Create environment → Get environment ID
- Install necessary packages (like pandas, matplotlib)
- Execute code (such as data analysis, chart generation)
- View execution results and generated file links

Code execution happens in a secure sandbox environment. Generated files (images, CSVs, etc.) will be automatically provided with download links.

Remeber not to show the image directly, do not use plt.plot() etc.
```