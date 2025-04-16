"""ast-grep tool implementations for the MCP server."""

import os
import subprocess
import json
import traceback
from typing import Dict, Any, List, Optional
from fastmcp import Context
import yaml

# Import common utilities
from src.tools.common.utils import (
    create_temp_file,
    get_language_extension,
    create_backup,
    is_path_safe
)

# Global variable to store the current project path
current_project_path = os.environ.get("PROJECT_PATH", "/project")

def validate_file_path(file_path: str, project_path: str) -> str:
    """
    Validate and construct the full file path.
    
    Args:
        file_path: Relative path to the file
        project_path: Base project path
        
    Returns:
        The full file path
        
    Raises:
        ValueError: If the file doesn't exist or is outside the project path
    """
    full_path = os.path.abspath(os.path.join(project_path, file_path))
    
    # Security check: ensure the path is within the project directory
    if not is_path_safe(full_path, project_path):
        raise ValueError(f"File path {file_path} is outside the project directory")
    
    # Check if the file exists
    if not os.path.isfile(full_path):
        raise ValueError(f"File {full_path} does not exist")
    
    return full_path

def run_ast_grep_command(
    cmd: List[str], 
    cwd: str, 
    expect_json: bool = True
) -> Dict[str, Any]:
    """
    Run an ast-grep command and process the output.
    
    Args:
        cmd: Command to run
        cwd: Working directory
        expect_json: Whether to expect JSON output
        
    Returns:
        Dictionary with command results
        
    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    process = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True
    )
    
    if expect_json and process.stdout.strip():
        return json.loads(process.stdout)
    
    return {
        "stdout": process.stdout,
        "stderr": process.stderr,
        "returncode": process.returncode
    }

def register_tools(mcp):
    """Register all ast-grep tools with the MCP server."""
    
    @mcp.tool()
    async def ast_grep_set_project_path(project_path: str, ctx: Context) -> Dict[str, Any]:
        """
        Set the project path for subsequent operations.
        
        Args:
            project_path: Path to the project directory
            ctx: MCP context for logging and progress reporting
        
        Returns:
            Confirmation of the set project path
        """
        global current_project_path
        
        await ctx.info(f"Setting project path to: {project_path}")
        
        try:
            # Use the provided path or fall back to the environment variable
            if project_path:
                if not os.path.isdir(project_path):
                    await ctx.error(f"Project path does not exist: {project_path}")
                    return {"success": False, "error": f"Directory not found: {project_path}"}
                current_project_path = project_path
            
            await ctx.info(f"Project path set to: {current_project_path}")
            return {"success": True, "project_path": current_project_path}
        except Exception as exc:
            await ctx.error(f"Error setting project path: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_parse_code(code: str, language: str, ctx: Context) -> Dict[str, Any]:
        """
        Parse the provided source code into an AST using ast-grep CLI.
        
        Args:
            code: The source code string to parse
            language: The language identifier (e.g., "python", "js", "ts")
            ctx: MCP context for logging and progress reporting
        
        Returns:
            A confirmation message
        """
        await ctx.info(f"Parsing {language} code with ast-grep...")
        
        try:
            # Create a temporary file for the code using common utility
            extension = get_language_extension(language)
            temp_file_path = create_temp_file(code, extension)
            
            # Prepare the command to check if the code is parseable
            # We use a simple pattern that should match any code
            cmd = ["ast-grep", "run", "-p", "$$$", "--json", temp_file_path]
            
            try:
                # Run the command
                results = run_ast_grep_command(cmd, os.getcwd())
                await ctx.info(f"Successfully parsed {len(code)} characters of {language} code")
                return {"success": True, "message": "AST parsed successfully"}
            except subprocess.CalledProcessError as e:
                await ctx.error(f"Failed to parse code: {e.stderr}")
                return {"success": False, "error": e.stderr}
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
        except Exception as exc:
            await ctx.error(f"Error parsing code: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_find_pattern(
        file_path: str, 
        pattern: str, 
        language: Optional[str] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Find AST nodes matching the given pattern using ast-grep CLI.
        
        Args:
            file_path: Path to the file to search, relative to the project path
            pattern: The AST query pattern (e.g., "print($ARG)")
            language: Optional language identifier (if not provided, will be inferred from file extension)
            ctx: MCP context for logging and progress reporting
        
        Returns:
            A list of matched node snippets
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Searching for pattern '{pattern}' in {file_path}...")
        
        try:
            # Validate and construct the full file path
            try:
                full_file_path = validate_file_path(file_path, current_project_path)
            except ValueError as e:
                await ctx.error(str(e))
                return {"success": False, "error": str(e)}
            
            # Prepare the command
            cmd = ["ast-grep", "run", "-p", pattern, "--json"]
            
            # Add language flag if specified
            if language:
                cmd.extend(["-l", language])
            
            # Add the file path
            cmd.append(full_file_path)
            
            # Run the command
            try:
                results = run_ast_grep_command(cmd, current_project_path)
                await ctx.info(f"Found {len(results)} matches")
                
                return {
                    "success": True, 
                    "matches": results,
                    "count": len(results)
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            
        except Exception as exc:
            await ctx.error(f"Error during find operation: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_replace_pattern(
        file_path: str,
        pattern: str,
        replacement: str,
        language: Optional[str] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Replace parts of the code using the given AST search pattern via ast-grep CLI.
        
        Args:
            file_path: Path to the file to modify, relative to the project path
            pattern: The AST search pattern (e.g., "print($MSG)")
            replacement: The replacement text (e.g., "logger.info($MSG)")
            language: Optional language identifier (if not provided, will be inferred from file extension)
            ctx: MCP context for logging and progress reporting
        
        Returns:
            The result of the replacement operation
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Replacing pattern '{pattern}' with '{replacement}' in {file_path}...")
        
        try:
            # Validate and construct the full file path
            try:
                full_file_path = validate_file_path(file_path, current_project_path)
            except ValueError as e:
                await ctx.error(str(e))
                return {"success": False, "error": str(e)}
            
            # Create a backup of the file using common utility
            backup_path = create_backup(full_file_path)
            await ctx.info(f"Created backup at {backup_path}")
            
            # Prepare the command with the update flag
            cmd = ["ast-grep", "run", "-p", pattern, "-r", replacement, "--update-all"]
            
            # Add language flag if specified
            if language:
                cmd.extend(["-l", language])
            
            # Add the file path
            cmd.append(full_file_path)
            
            # Run the command
            try:
                run_ast_grep_command(cmd, current_project_path, expect_json=False)
                
                # Verify the file was actually changed
                with open(full_file_path, 'r', encoding='utf-8') as f:
                    updated_content = f.read()
                
                # Check if the pattern is still in the file and the replacement is not
                # This is a simplistic check and might not work for all cases
                if pattern in updated_content and replacement not in updated_content:
                    await ctx.warning("File content appears unchanged despite successful command execution")
                    return {
                        "success": False,
                        "error": "File content was not modified as expected"
                    }
                
                await ctx.info(f"Replacement completed successfully")
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "replacements": "Completed",
                    "backup_path": os.path.basename(backup_path)
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            
        except Exception as exc:
            await ctx.error(f"Error during replace operation: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_run_yaml_rule(
        file_path: str,
        rule_yaml: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Run a custom lint or transformation rule specified in YAML using ast-grep CLI.
        
        Args:
            file_path: Path to the file to analyze, relative to the project path
            rule_yaml: The custom rule configuration as a YAML string
            ctx: MCP context for logging and progress reporting
        
        Returns:
            The results of executing the rule
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Running YAML rule on {file_path}...")
        
        try:
            # Validate and construct the full file path
            try:
                full_file_path = validate_file_path(file_path, current_project_path)
            except ValueError as e:
                await ctx.error(str(e))
                return {"success": False, "error": str(e)}
            
            # Validate the YAML rule
            try:
                rule_config = yaml.safe_load(rule_yaml)
                if not isinstance(rule_config, dict) or 'rule' not in rule_config:
                    raise ValueError("Invalid rule YAML: missing 'rule' section")
            except Exception as e:
                await ctx.error(f"Invalid rule YAML: {str(e)}")
                return {"success": False, "error": f"Invalid rule YAML: {str(e)}"}
            
            # Create a temporary file for the YAML rule
            rule_path = create_temp_file(rule_yaml, '.yml')
            
            # Create a backup of the file
            backup_path = create_backup(full_file_path)
            
            # Prepare the command to run the rule with update flag
            cmd = ["ast-grep", "run", "--rule", rule_path, "--json", "--update-all", full_file_path]
            
            try:
                results = run_ast_grep_command(cmd, current_project_path)
                await ctx.info(f"Rule execution completed successfully")
                
                return {
                    "success": True,
                    "results": results,
                    "file_path": file_path,
                    "backup_path": os.path.basename(backup_path)
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            finally:
                # Clean up the temporary rule file
                os.unlink(rule_path)
            
        except Exception as exc:
            await ctx.error(f"Error running rule: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_scan_project(
        pattern: Optional[str] = None,
        rule_yaml: Optional[str] = None,
        file_glob: Optional[str] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Scan the entire project for patterns or rule violations.
        
        Args:
            pattern: Optional pattern to search for
            rule_yaml: Optional YAML rule to apply
            file_glob: Optional glob pattern to filter files (e.g., "*.cs")
            ctx: MCP context for logging and progress reporting
        
        Returns:
            The results of the scan
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Scanning project at {current_project_path}...")
        
        try:
            # Prepare the command
            cmd = ["ast-grep"]
            rule_path = None
            
            if pattern:
                # Use run command with pattern
                cmd.extend(["run", "-p", pattern, "--json"])
            elif rule_yaml:
                # Validate the YAML rule
                try:
                    rule_config = yaml.safe_load(rule_yaml)
                    if not isinstance(rule_config, dict) or 'rule' not in rule_config:
                        raise ValueError("Invalid rule YAML: missing 'rule' section")
                except Exception as e:
                    await ctx.error(f"Invalid rule YAML: {str(e)}")
                    return {"success": False, "error": f"Invalid rule YAML: {str(e)}"}
                
                # Create a temporary file for the YAML rule
                rule_path = create_temp_file(rule_yaml, '.yml')
                
                # Use run command with rule
                cmd.extend(["run", "--rule", rule_path, "--json"])
            else:
                # Check if sgconfig.yml exists
                sgconfig_path = os.path.join(current_project_path, "sgconfig.yml")
                if not os.path.isfile(sgconfig_path):
                    await ctx.error("No pattern, rule, or sgconfig.yml found. Cannot perform scan.")
                    return {
                        "success": False, 
                        "error": "No pattern, rule, or sgconfig.yml found. Cannot perform scan."
                    }
                
                # Use scan command (requires sgconfig.yml)
                cmd.append("scan")
                cmd.append("--json")
            
            # Add file glob if specified
            if file_glob:
                cmd.append(file_glob)
            
            # Run the command
            try:
                results = run_ast_grep_command(cmd, current_project_path)
                if not isinstance(results, list):
                    results = [results]
                    
                await ctx.info(f"Scan completed successfully. Found {len(results)} matches/issues.")
                
                return {
                    "success": True,
                    "results": results,
                    "count": len(results)
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            finally:
                # Clean up temporary rule file if created
                if rule_path and os.path.exists(rule_path):
                    os.unlink(rule_path)
            
        except Exception as exc:
            await ctx.error(f"Error during project scan: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_initialize_project(ctx: Context = None) -> Dict[str, Any]:
        """
        Initialize a new ast-grep project in the current directory.
        Creates sgconfig.yml and a rules directory with example rules.
        
        Returns:
            Status of the initialization
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Initializing ast-grep project in {current_project_path}...")
        
        try:
            # Check if sgconfig.yml already exists
            sgconfig_path = os.path.join(current_project_path, "sgconfig.yml")
            if os.path.exists(sgconfig_path):
                await ctx.warning("sgconfig.yml already exists. Skipping initialization.")
                return {
                    "success": True,
                    "message": "Project already initialized",
                    "status": "skipped"
                }
            
            # Prepare the command
            cmd = ["ast-grep", "new"]
            
            try:
                result = run_ast_grep_command(cmd, current_project_path, expect_json=False)
                await ctx.info("Project initialization completed successfully")
                
                return {
                    "success": True,
                    "message": "ast-grep project initialized successfully",
                    "output": result.get("stdout", "")
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep new command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            
        except Exception as exc:
            await ctx.error(f"Error during project initialization: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
    
    @mcp.tool()
    async def ast_grep_test_rule(
        rule_path: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Test an ast-grep rule using the test command.
        
        Args:
            rule_path: Path to the rule file, relative to the project path
            ctx: MCP context for logging and progress reporting
        
        Returns:
            The test results
        """
        global current_project_path
        if not current_project_path:
            return {"success": False, "error": "Project path not set. Call set_project_path first."}
        
        await ctx.info(f"Testing rule {rule_path}...")
        
        try:
            # Validate and construct the full rule path
            try:
                full_rule_path = validate_file_path(rule_path, current_project_path)
            except ValueError as e:
                await ctx.error(str(e))
                return {"success": False, "error": str(e)}
            
            # Prepare the command
            cmd = ["ast-grep", "test", full_rule_path, "--json"]
            
            try:
                results = run_ast_grep_command(cmd, current_project_path)
                await ctx.info(f"Rule test completed successfully")
                
                return {
                    "success": True,
                    "results": results
                }
            except subprocess.CalledProcessError as e:
                await ctx.error(f"ast-grep test command failed: {e.stderr}")
                return {"success": False, "error": e.stderr}
            
        except Exception as exc:
            await ctx.error(f"Error during rule test: {str(exc)}")
            return {"success": False, "error": str(exc), "trace": traceback.format_exc()}
