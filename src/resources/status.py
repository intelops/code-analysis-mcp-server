"""System status resource for the MCP server."""

from typing import Dict, Any

def register_status_resource(mcp):
    """Register the system status resource with the MCP server."""
    
    @mcp.resource("system://status")
    async def get_system_status() -> Dict[str, Any]:
        """
        Provide system status information about the Code Analysis MCP server.
        
        Returns:
            Status information including version details
        """
        try:
            import ast_grep_py
            import fastmcp
            
            # Get version information
            ast_grep_version = getattr(ast_grep_py, "__version__", "unknown")
            fastmcp_version = getattr(fastmcp, "__version__", "unknown")
            
            # Get available tools
            available_tools = {
                "ast_grep": [
                    "ast_grep_parse_code",
                    "ast_grep_find_pattern",
                    "ast_grep_replace_pattern",
                    "ast_grep_run_yaml_rule"
                ]
                # Future tools will be added here
            }
            
            return {
                "status": "operational",
                "ast_grep_py_version": ast_grep_version,
                "fastmcp_version": fastmcp_version,
                "supported_languages": [
                    "python", "javascript", "typescript", "rust", 
                    "go", "java", "c", "cpp", "csharp"
                ],
                "available_tools": available_tools
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "error": str(exc)
            }
