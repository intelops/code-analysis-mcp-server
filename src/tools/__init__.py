"""Tool registration for the MCP server."""

def register_all_tools(mcp):
    """Register all available tools with the MCP server."""
    # Import and register ast-grep tools
    from src.tools.ast_grep.tools import register_tools as register_ast_grep_tools
    register_ast_grep_tools(mcp)
    
    # In the future, you can add more tool registrations here:
    # from src.tools.semgrep.tools import register_tools as register_semgrep_tools
    # register_semgrep_tools(mcp)
    
    # from src.tools.pylint.tools import register_tools as register_pylint_tools
    # register_pylint_tools(mcp)
