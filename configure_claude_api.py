#!/usr/bin/env python3
"""
Configure Claude API key for YOLO services
"""

import os
import sys
from pathlib import Path

def configure_claude_api():
    """Configure the Claude API key from .env.production"""
    
    # Read the production environment file
    env_prod_path = Path(__file__).parent / '.env.production'
    if not env_prod_path.exists():
        print("Error: .env.production file not found!")
        return False
    
    # Extract the Claude API key
    api_key = None
    with open(env_prod_path, 'r') as f:
        for line in f:
            if line.strip().startswith('CLAUDE_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                break
    
    if not api_key:
        print("Error: CLAUDE_API_KEY not found in .env.production!")
        return False
    
    # Create or update .env file with Claude API key
    env_path = Path(__file__).parent / 'flask_app' / '.env'
    env_content = []
    
    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    
    # Update or add Claude API key
    claude_key_found = False
    anthropic_key_found = False
    
    for i, line in enumerate(env_content):
        if line.strip().startswith('CLAUDE_API_KEY='):
            env_content[i] = f'CLAUDE_API_KEY={api_key}\n'
            claude_key_found = True
        elif line.strip().startswith('ANTHROPIC_API_KEY='):
            env_content[i] = f'ANTHROPIC_API_KEY={api_key}\n'
            anthropic_key_found = True
    
    # Add keys if not found
    if not claude_key_found:
        env_content.append(f'CLAUDE_API_KEY={api_key}\n')
    if not anthropic_key_found:
        env_content.append(f'ANTHROPIC_API_KEY={api_key}\n')
    
    # Write the updated .env file
    with open(env_path, 'w') as f:
        f.writelines(env_content)
    
    print(f"Successfully configured Claude API key in {env_path}")
    
    # Also set environment variable for current session
    os.environ['CLAUDE_API_KEY'] = api_key
    os.environ['ANTHROPIC_API_KEY'] = api_key
    
    return True

if __name__ == "__main__":
    success = configure_claude_api()
    sys.exit(0 if success else 1)