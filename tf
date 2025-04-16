#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from datetime import datetime

def get_workspace():
    """Get current Terraform workspace. If no workspace is specified, list available workspaces"""
    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == 'workspace'):
        result = subprocess.run([get_terraform_binary(), 'workspace', 'list'], 
                          capture_output=False, text=True)
        sys.exit(0)
    
    try:
        result = subprocess.run([get_terraform_binary(), 'workspace', 'show'], 
                          capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return 'default'

def setup_workspace_directories(workspace):
    """Setup required directories and files for the workspace"""
    cwd = os.getcwd()
    
    # Create varfiles directory
    varfiles_dir = f"{cwd}/varfiles"
    os.makedirs(varfiles_dir, exist_ok=True)
    
    # Create workspace tfvars file
    varfile = f"{varfiles_dir}/{workspace}.tfvars"
    if not os.path.exists(varfile):
        open(varfile, 'w').close()
    
    # Create workspace JSON file for environment variables if it doesn't exist
    json_file = f"{varfiles_dir}/{workspace}.json"
    if not os.path.exists(json_file):
        with open(json_file, 'w') as f:
            json.dump({}, f, indent=2)
    
    # Create and set TF_DATA_DIR
    data_dir = f"{cwd}/terraform_data_dirs/{workspace}"
    os.makedirs(data_dir, exist_ok=True)
    os.environ['TF_DATA_DIR'] = data_dir
    
    # Set environment variables
    os.environ['TF_VARFILE'] = varfile

def cleanup_workspace_files(workspace):
    """Clean up workspace-related files when a workspace is deleted"""
    cwd = os.getcwd()
    
    # Remove varfiles
    varfile = f"{cwd}/varfiles/{workspace}.tfvars"
    json_file = f"{cwd}/varfiles/{workspace}.json"
    
    try:
        if os.path.exists(varfile):
            os.remove(varfile)
        if os.path.exists(json_file):
            os.remove(json_file)
            
        # Remove terraform data directory
        data_dir = f"{cwd}/terraform_data_dirs/{workspace}"
        if os.path.exists(data_dir):
            import shutil
            shutil.rmtree(data_dir)
    except Exception as e:
        print(f"Warning: Error cleaning up workspace files: {e}", file=sys.stderr)

def get_git_commit_info():
    """Get current git commit information"""
    try:
        commit_hash = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                   capture_output=True, text=True, check=True).stdout.strip()
        commit_msg = subprocess.run(['git', 'log', '-1', '--pretty=%B'],
                                  capture_output=True, text=True, check=True).stdout.strip()
        author = subprocess.run(['git', 'log', '-1', '--pretty=%an'],
                              capture_output=True, text=True, check=True).stdout.strip()
        return {
            'commit_hash': commit_hash,
            'commit_message': commit_msg,
            'author': author,
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.CalledProcessError:
        return None

def save_commit_info(commit_info):
    """Save commit information to .terraform_commits in current directory"""
    commits_file = os.path.join(os.getcwd(), '.terraform_commits')
    try:
        with open(commits_file, 'r') as f:
            commits = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        commits = []
    
    commits.append(commit_info)
    
    with open(commits_file, 'w') as f:
        json.dump(commits, f, indent=2)

def load_workspace_env_from_json(workspace):
    """Load environment variables from workspace-specific JSON file if it exists
    
    Args:
        workspace (str): The terraform workspace name
        
    Returns:
        bool: True if JSON file was loaded successfully, False otherwise
    """
    json_file = f"{os.getcwd()}/varfiles/{workspace}.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                env_vars = json.load(f)
            
            if not isinstance(env_vars, dict):
                return False
            
            # Add each variable to environment silently
            for key, value in env_vars.items():
                if isinstance(value, (str, int, float, bool)):
                    os.environ[key] = str(value)
                else:
                    os.environ[key] = json.dumps(value)
            return True
        except (json.JSONDecodeError, Exception):
            return False
    return False

def set_terraform_env(workspace):
    """Set Terraform environment variables based on workspace"""
    varfile = f"{os.getcwd()}/varfiles/{workspace}.tfvars"
    
    if os.path.exists(varfile):
        var_file_arg = f"-var-file={varfile}"
        # Set var-file for relevant commands
        os.environ['TF_CLI_ARGS_plan'] = var_file_arg
        os.environ['TF_CLI_ARGS_apply'] = var_file_arg
        os.environ['TF_CLI_ARGS_import'] = var_file_arg
        os.environ['TF_CLI_ARGS_destroy'] = var_file_arg
        # Set the varfile path in environment for reference
        os.environ['TF_VARFILE'] = varfile

def get_terraform_binary():
    """Get the terraform binary path"""
    # Check for environment variable override
    tf_binary = os.getenv('TERRAFORM_BINARY')
    if tf_binary and os.path.exists(tf_binary):
        return tf_binary
    
    # Default path
    default_binary = os.path.expanduser('~/git/tfenv/bin/terraform')
    return default_binary if os.path.exists(default_binary) else 'terraform'

def write_workspace_info(workspace):
    """Write workspace and color information to hidden file"""
    # Get color from JSON config if it exists
    color = "37"  # Default to white
    json_file = f"{os.getcwd()}/varfiles/{workspace}.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                env_vars = json.load(f)
                if "TF_WORKSPACE_COLOR" in env_vars:
                    color = env_vars["TF_WORKSPACE_COLOR"]
        except (json.JSONDecodeError, Exception):
            pass
    
    # Write workspace info to hidden file
    ws_file = os.path.expanduser('~/.tf_workspace_info')
    with open(ws_file, 'w') as f:
        f.write(f"TF_WORKSPACE_NAME={workspace}\n")
        f.write(f"TF_WORKSPACE_COLOR={color}\n")

def run_terraform(args):
    """Run Terraform command with given arguments"""
    terraform_bin = get_terraform_binary()
    workspace = get_workspace()
    varfile = f"{os.getcwd()}/varfiles/{workspace}.tfvars"
    
    # Create a copy of the current environment
    env = os.environ.copy()
    
    # Load workspace-specific environment variables
    json_file = f"{os.getcwd()}/varfiles/{workspace}.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                workspace_env = json.load(f)
            
            if isinstance(workspace_env, dict):
                # Add each variable to the environment
                for key, value in workspace_env.items():
                    if isinstance(value, (str, int, float, bool)):
                        env[key] = str(value)
                    else:
                        env[key] = json.dumps(value)
        except (json.JSONDecodeError, Exception):
            pass
    
    # Handle workspace commands
    if args and args[0] == 'workspace' and len(args) > 1:
        if args[1] == 'new':
            # Create workspace
            cmd = [terraform_bin, 'workspace', 'new', args[2]]
            result = subprocess.run(cmd, env=env)
            if result.returncode == 0:
                setup_workspace_directories(args[2])
                write_workspace_info(args[2])
            return result.returncode
        elif args[1] == 'select':
            # Try to select or create workspace
            cmd = [terraform_bin, 'workspace', 'select', '-or-create', args[2]]
            result = subprocess.run(cmd, env=env)
            if result.returncode == 0:
                setup_workspace_directories(args[2])
                write_workspace_info(args[2])
            return result.returncode
    
    # Add var-file argument for relevant commands if varfile exists
    cmd = [terraform_bin] + args
    if os.path.exists(varfile) and args and args[0] in ['plan', 'apply', 'import', 'destroy']:
        cmd.append(f'-var-file={varfile}')
    
    result = subprocess.run(cmd, env=env)
    return result.returncode

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    args = sys.argv[1:]
    command = args[0]
    
    # Handle workspace delete command
    if command == 'workspace' and len(args) > 2 and args[1] == 'delete':
        workspace_to_delete = args[2]
        # Run terraform workspace delete first
        result = run_terraform(args)
        if result == 0:
            # If terraform delete succeeded, clean up the files
            cleanup_workspace_files(workspace_to_delete)
        return result

    # Get workspace first
    workspace = get_workspace()
    
    # Always ensure workspace directories are set up
    setup_workspace_directories(workspace)
    
    # Load workspace-specific environment from JSON file silently
    load_workspace_env_from_json(workspace)
    
    set_terraform_env(workspace)

    # Handle apply with targets
    if command == 'apply' and os.path.exists('.targets'):
        with open('.targets', 'r') as f:
            targets = f.read().splitlines()
        
        for target in targets:
            target_args = ['apply', f'-target={target}'] + args[1:]
            if run_terraform(target_args) != 0:
                sys.exit(1)
    
    # Run the main terraform command
    result = run_terraform(args)
    
    # If it's a successful apply, save the git commit info silently
    if result == 0 and command == 'apply':
        commit_info = get_git_commit_info()
        if commit_info:
            save_commit_info(commit_info)
    
    sys.exit(result)

if __name__ == '__main__':
    main()
