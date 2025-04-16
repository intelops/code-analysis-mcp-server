# Code Analysis MCP Server
A modular Model Context Protocol (MCP) server for code analysis tools, with a primary focus on ast-grep integration. This server provides a standardized interface for AI assistants and other clients to perform structural code queries and transformations.

## Features
- **Structural Code Analysis**: Find patterns in code using ast-grep's powerful pattern matching capabilities

- **Code Transformations**: Replace patterns in code with new implementations

- **YAML Rule Support**: Apply custom lint and transformation rules defined in YAML

- **Project-Wide Scanning**: Scan entire projects for patterns or rule violations

- **Containerized Deployment**: Easy deployment with Docker

- **Modular Architecture**: Designed for easy extension with additional code analysis tools

## Requirements
- Python 3.12.8

- ast-grep CLI tool

- Docker (for containerized deployment)

## Installation
**Using pip**

```bash
pip install code-analysis-mcp-server
```

**From source**
```bash
git clone https://github.com/yourusername/code-analysis-mcp-server.git
cd code-analysis-mcp-server
pip install -e .
```

**Using Docker**
```bash
docker pull yourusername/code-analysis-mcp-server
# or build locally
docker build -t code-analysis-mcp-server .
```

## Usage
### Starting the server
```bash
# Direct execution
code-analysis-server

# With Docker
docker run -p 8000:8000 -v /path/to/your/project:/project code-analysis-mcp-server
```

### Using with Docker Compose  
**Create a docker-compose.yml file:**
```text
version: '3'

services:
  code-analysis-mcp:
    image: yourusername/code-analysis-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ${PROJECT_DIR:-./sample_project}:/project
    environment:
      - PROJECT_PATH=/project
    restart: unless-stopped
```
**Then run:**
```bash
PROJECT_DIR=/path/to/your/project docker-compose up -d
```

**Client Example**
```python
import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import SSETransport

async def main():
    async with Client(transport=SSETransport("http://localhost:8000/sse")) as client:
        # Set project path
        project_result = await client.call_tool(
            "ast_grep_set_project_path",
            {
                "project_path": "/project"
            }
        )
        
        # Process the result correctly
        content_item = project_result[0]
        result_data = json.loads(content_item.text)
        print("Project path result:", result_data)
        
        # Find patterns in a file
        find_result = await client.call_tool(
            "ast_grep_find_pattern",
            {
                "file_path": "src/example.cs",
                "pattern": "public class $NAME"
            }
        )
        
        # Process results
        content_item = find_result[0]
        result_data = json.loads(content_item.text)
        print(f"Found {result_data.get('count', 0)} matches")

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools
The server provides the following tools:
### ast-grep
- **ast_grep_set_project_path:** Set the project path for subsequent operations
- **ast_grep_parse_code:** Parse code into an AST
- **ast_grep_find_pattern:** Find patterns in code files
- **ast_grep_replace_pattern:** Replace patterns in code files
- **ast_grep_run_yaml_rule:** Run custom YAML rules on code files
- **ast_grep_scan_project:** Scan entire projects for patterns or rule violations
- **ast_grep_initialize_project:** Initialize a new ast-grep project
- **ast_grep_test_rule:** Test ast-grep rules

## Supported Languages
- Python
- JavaScript
- TypeScript
- Rust
- Go
- Java
- C
- C++
- C#

## Project Structure
```text
code-analysis-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py                # Main MCP server setup
│   ├── tools/
│   │   ├── __init__.py          # Tool registration
│   │   ├── ast_grep/
│   │   │   ├── __init__.py
│   │   │   ├── tools.py         # ast-grep tool implementations
│   │   └── common/
│   │       ├── __init__.py
│   │       └── utils.py         # Shared utilities
│   └── resources/
│       ├── __init__.py
│       └── status.py            # System status resource
├── tests/
├── pyproject.toml
├── setup.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

```text
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```