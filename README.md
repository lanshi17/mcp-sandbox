# MCP Sandbox

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/release/python-3120/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-blueviolet)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-Compatible-brightgreen)](https://github.com/estitesc/mission-control-link)

[中文文档](README_zh.md) | English

Python MCP Sandbox is an interactive Python code execution tool that allows users and LLMs to safely execute Python code and install packages in isolated Docker containers.

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

1. **create_python_env**: Creates a new Python Docker container and returns its ID for subsequent code execution and package installation
2. **execute_python_code**: Executes Python code in a specified Docker container
3. **install_package_in_env**: Installs Python packages in a specified Docker container
4. **check_package_status**: Checks if a package is installed or installation status in a Docker container

## Project Structure

```
python-mcp-sandbox/
├── main.py                    # Application entry point
├── requirements.txt           # Project dependencies
├── Dockerfile                 # Docker configuration for Python containers
├── results/                   # Directory for generated files
├── mcp_sandbox/               # Main package directory
│   ├── __init__.py
│   ├── models.py              # Pydantic models
│   ├── api/                   # API related components
│   │   ├── __init__.py
│   │   └── routes.py          # API route definitions
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── docker_manager.py  # Docker container management
│   │   └── python_service.py  # Python execution service
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── config.py          # Configuration constants
│       ├── file_manager.py    # File management
│       └── task_manager.py    # Periodic task management
└── README.md                  # Project documentation
```

## Example Prompt
```
I've configured a Python code execution environment for you. You can run Python code using the following steps:

1. First, use the "create_python_env" tool to create a virtual environment
   - This will return a container_id which you'll need for subsequent operations

2. If you need to install packages, use the "install_package_in_env" tool
   - Parameters: container_id and package_name (e.g., numpy, pandas)
   - This starts asynchronous installation and returns immediately with status

3. After installing packages, you can check their installation status using the "check_package_status" tool
   - Parameters: container_id and package_name (name of the package to check)
   - If the package is still installing, you need to check again using this tool

4. Use the "execute_python_code" tool to run your code
   - Parameters: container_id and code (Python code)
   - Returns output, errors and links to any generated files

Example workflow:
- Use create_python_env → Get container_id
- Use install_package_in_env to install necessary packages (like pandas, matplotlib), with the container_id parameter
- Use check_package_status to verify package installation, with the same container_id parameter
- Use execute_python_code to run your code, with the container_id parameter
- View execution results and generated file links

Code execution happens in a secure sandbox environment. Generated files (images, CSVs, etc.) will be automatically provided with download links.

Remember not to show the image directly in the Python code. For visualizations:
- Save figures to files using plt.savefig() instead of plt.show()
- For data, use methods like df.to_csv() or df.to_excel() to save as files
- All saved files will automatically appear as download links in the results
```
