#!/usr/bin/env python3
"""
Setup script for AI Agent Context Management System

This script helps set up the development environment for the project.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and handle errors gracefully."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    prerequisites = {
        "python3 --version": "Python 3.8+",
        "git --version": "Git",
        "claude --version": "Claude Code CLI"
    }
    
    missing = []
    for command, name in prerequisites.items():
        try:
            subprocess.run(command.split(), capture_output=True, check=True)
            print(f"✅ {name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {name} is missing")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing prerequisites: {', '.join(missing)}")
        print("Please install the missing tools before continuing.")
        return False
    
    print("✅ All prerequisites are installed")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    if not run_command("python3 -m venv venv", "Creating virtual environment"):
        return False
    
    # Activate virtual environment and upgrade pip
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && python -m pip install --upgrade pip"
    else:  # Unix/MacOS
        activate_cmd = "source venv/bin/activate && python -m pip install --upgrade pip"
    
    return run_command(activate_cmd, "Upgrading pip in virtual environment")

def install_dependencies(dev_mode=False):
    """Install Python dependencies."""
    requirements_file = "requirements-dev.txt" if dev_mode else "requirements.txt"
    
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Unix/MacOS
        activate_cmd = "source venv/bin/activate"
    
    install_cmd = f"{activate_cmd} && pip install -r {requirements_file}"
    
    description = f"Installing {'development' if dev_mode else 'production'} dependencies"
    return run_command(install_cmd, description)

def create_env_file():
    """Create .env file for environment variables."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_content = """# AI Agent Context Management System Environment Variables

# Database Configuration
DATABASE_URL=sqlite:///context_management.db
VECTOR_DB_URL=chroma://./chroma_db

# MCP Server Configuration
CONTEXT_STORAGE_PORT=8001
RETRIEVAL_ENGINE_PORT=8002
INTELLIGENCE_ENGINE_PORT=8003
SESSION_MANAGER_PORT=8004

# Intelligence Settings
LEARNING_RATE=0.01
CONFIDENCE_THRESHOLD=0.7
PATTERN_MIN_USAGE=3

# Development Settings
DEBUG=true
LOG_LEVEL=INFO

# API Keys (optional - for cloud features)
# OPENAI_API_KEY=your_openai_api_key_here
# PINECONE_API_KEY=your_pinecone_api_key_here
"""
    
    try:
        env_file.write_text(env_content)
        print("✅ Created .env file with default configuration")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def setup_git_hooks():
    """Set up git hooks for development."""
    if not Path(".git").exists():
        print("⚠️  Not a git repository, skipping git hooks setup")
        return True
    
    # Install pre-commit hooks
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Unix/MacOS
        activate_cmd = "source venv/bin/activate"
    
    hook_cmd = f"{activate_cmd} && pre-commit install"
    return run_command(hook_cmd, "Setting up pre-commit hooks")

def create_basic_directories():
    """Create basic directory structure if it doesn't exist."""
    directories = [
        "src/servers",
        "src/intelligence", 
        "src/bootstrap",
        "src/integration",
        "config/environments",
        "config/schemas",
        "tests/unit",
        "tests/integration", 
        "tests/e2e",
        "examples/projects",
        "examples/patterns",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created project directory structure")
    return True

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup AI Agent Context Management System")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--skip-checks", action="store_true", help="Skip prerequisite checks")
    
    args = parser.parse_args()
    
    print("🚀 AI Agent Context Management System Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not args.skip_checks and not check_prerequisites():
        sys.exit(1)
    
    # Interactive mode
    if args.interactive:
        print("\n📋 Setup Options:")
        print("1. Basic setup (production dependencies)")
        print("2. Development setup (includes dev tools and optional ML libraries)")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "2":
            args.dev = True
    
    # Setup steps
    steps = [
        ("Creating directory structure", create_basic_directories),
        ("Setting up virtual environment", setup_virtual_environment),
        ("Installing dependencies", lambda: install_dependencies(args.dev)),
        ("Creating environment file", create_env_file),
        ("Setting up git hooks", setup_git_hooks),
    ]
    
    failed_steps = []
    for description, step_func in steps:
        if not step_func():
            failed_steps.append(description)
    
    # Summary
    print("\n" + "=" * 50)
    if failed_steps:
        print("⚠️  Setup completed with issues:")
        for step in failed_steps:
            print(f"   ❌ {step}")
        print("\nPlease resolve the issues above and run the setup again.")
    else:
        print("🎉 Setup completed successfully!")
        
        print("\n📝 Next steps:")
        print("1. Activate the virtual environment:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("2. Start Phase 1 - Architecture Design:")
        print("   claude-code --project ClaudeContextMCP")
        print("3. Use the architecture prompt from IMPLEMENTATION_ROADMAP.md")
        
        print("\n🔧 Configuration:")
        print("- Environment variables: .env file")
        print("- MCP servers will run on ports 8001-8004")
        print("- Database: SQLite (local) or PostgreSQL (production)")
        print("- Vector DB: Chroma (local) or Pinecone (cloud)")

if __name__ == "__main__":
    main()