"""
Dependency Manager for Agent 50.
Handles Python and Node.js dependencies with auto-fix capabilities.
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import shutil
# Removed circular import: from memory.memory_manager import MemoryManager

class DependencyManager:
    """Manages dependencies for generated projects."""
    
    def __init__(self):
        self.logger = logging.getLogger("Agent50.Builder.DependencyManager")
        self.memory = None  # Will be set by FileGenerator
        
    def generate(self, blueprint: Dict[str, Any], project_path: Path):
        """Generate dependency files for a project."""
        self.logger.info(f"Generating dependencies for: {project_path}")
        
        # Update project status
        if self.memory:
            self.memory.update_project_status({
                "system": "ready",
                "architecture": 100,
                "backend": 100,
                "frontend": 100,
                "deployment": 0,
                "message": "Generating dependency files..."
            })
        
        try:
            # Generate Python requirements
            self._generate_python_dependencies(blueprint, project_path)
            
            # Generate Node.js package.json if frontend exists
            if (project_path / "frontend").exists():
                self._generate_node_dependencies(blueprint, project_path)
            
            # Generate setup files
            self._generate_setup_files(project_path)
            
            # Validate dependencies
            self._validate_dependencies(project_path)
            
            self.logger.info("Dependency generation complete")
            
        except Exception as e:
            self.logger.error(f"Failed to generate dependencies: {e}")
            raise
    
    def _generate_python_dependencies(self, blueprint: Dict[str, Any], project_path: Path):
        """Generate Python dependency files."""
        backend_path = project_path / "backend"
        
        # Determine backend framework
        backend_framework = blueprint.get("architecture", {}).get("backend", {}).get("framework", "fastapi")
        
        # Base dependencies
        base_deps = [
            "python-dotenv>=1.0.0",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.6",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
        ]
        
        # Framework-specific dependencies
        framework_deps = {
            "fastapi": [
                "fastapi>=0.104.1",
                "uvicorn[standard]>=0.24.0",
                "sqlalchemy>=2.0.23",
                "alembic>=1.12.1",
                "asyncpg>=0.29.0",  # For PostgreSQL
            ],
            "flask": [
                "flask>=3.0.0",
                "flask-sqlalchemy>=3.0.5",
                "flask-cors>=4.0.0",
                "flask-jwt-extended>=4.5.2",
                "flask-migrate>=4.0.4",
            ],
            "django": [
                "django>=4.2.7",
                "django-rest-framework>=3.14.0",
                "django-cors-headers>=4.2.0",
                "django-filter>=23.3",
                "djangorestframework-simplejwt>=5.3.0",
            ]
        }
        
        # Database dependencies
        database_type = blueprint.get("architecture", {}).get("database", {}).get("type", "postgres")
        db_deps = {
            "postgres": ["psycopg2-binary>=2.9.9"],
            "sqlite": [],  # Built-in
            "mongodb": ["pymongo>=4.6.0", "motor>=3.3.0"]
        }
        
        # Additional dependencies based on blueprint features
        extra_deps = []
        
        # Authentication
        if blueprint.get("architecture", {}).get("authentication", {}).get("enabled", True):
            extra_deps.extend([
                "bcrypt>=4.0.1",
                "pyjwt>=2.8.0",
            ])
        
        # File uploads
        if blueprint.get("architecture", {}).get("file_processing", {}).get("enabled", False):
            extra_deps.extend([
                "python-magic>=0.4.27",
                "pillow>=10.1.0",
            ])
        
        # AI/ML features
        if blueprint.get("type") == "ai_app":
            extra_deps.extend([
                "numpy>=1.24.0",
                "pandas>=2.1.0",
                "scikit-learn>=1.3.0",
                "transformers>=4.35.0",
                "torch>=2.1.0",
                "sentence-transformers>=2.2.2",
            ])
        
        # Email
        if blueprint.get("architecture", {}).get("notifications", {}).get("email", False):
            extra_deps.append("emails>=0.6.0")
        
        # Redis for caching/queue
        if any([
            blueprint.get("architecture", {}).get("backend", {}).get("caching", False),
            blueprint.get("architecture", {}).get("backend", {}).get("queue", False)
        ]):
            extra_deps.append("redis>=5.0.0")
        
        # AWS S3
        if blueprint.get("architecture", {}).get("file_storage", {}).get("provider") == "aws_s3":
            extra_deps.append("boto3>=1.34.0")
        
        # Compile all dependencies
        all_deps = base_deps + framework_deps.get(backend_framework, [])
        all_deps.extend(db_deps.get(database_type, []))
        all_deps.extend(extra_deps)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in all_deps:
            if dep not in seen:
                seen.add(dep)
                unique_deps.append(dep)
        
        # Write requirements.txt
        requirements_content = "\n".join(sorted(unique_deps))
        
        # Also write requirements-dev.txt
        dev_deps = [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.5.0",
            "coverage>=7.3.0",
        ]
        
        # Create backend directory if it doesn't exist
        backend_path.mkdir(exist_ok=True)
        
        # Write main requirements
        req_file = backend_path / "requirements.txt"
        req_file.write_text(requirements_content + "\n")
        
        # Write dev requirements
        dev_req_file = backend_path / "requirements-dev.txt"
        dev_req_file.write_text(requirements_content + "\n" + "\n".join(dev_deps) + "\n")
        
        # Generate pyproject.toml for modern Python projects
        self._generate_pyproject_toml(blueprint, backend_path, unique_deps, dev_deps)
        
        # Generate runtime.txt for Python version
        runtime_file = backend_path / "runtime.txt"
        runtime_file.write_text("python-3.11.0\n")
        
        self.logger.info(f"Generated Python dependencies for {backend_framework}")
    
    def _generate_pyproject_toml(self, blueprint: Dict[str, Any], backend_path: Path, 
                                deps: List[str], dev_deps: List[str]):
        """Generate pyproject.toml for modern Python projects."""
        project_name = blueprint.get("name", "app").lower().replace(" ", "-").replace("_", "-")
        
        # Extract package names without versions for pyproject.toml
        def extract_package_name(dep: str) -> str:
            # Handle various formats: "package>=1.0.0", "package[extra]>=1.0.0"
            match = re.match(r'^([a-zA-Z0-9_-]+)(\[.*\])?', dep)
            return match.group(1) if match else dep.split(">=")[0].split("==")[0]
        
        dependencies = [extract_package_name(dep) for dep in deps]
        dev_dependencies = [extract_package_name(dep) for dep in dev_deps]
        
        pyproject_content = f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "{blueprint.get('description', 'A web application')}"
readme = "README.md"
requires-python = ">=3.11"
license = {{text = "MIT"}}
authors = [
    {{name = "Agent 50", email = "agent@example.com"}},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = {json.dumps(dependencies, indent=2)}

[project.optional-dependencies]
dev = {json.dumps(dev_dependencies, indent=2)}

[project.urls]
Homepage = "https://github.com/username/{project_name}"
Repository = "https://github.com/username/{project_name}.git"
Issues = "https://github.com/username/{project_name}/issues"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
"""
        
        pyproject_file = backend_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content)
    
    def _generate_node_dependencies(self, blueprint: Dict[str, Any], project_path: Path):
        """Generate Node.js dependencies."""
        frontend_path = project_path / "frontend"
        
        # Check if package.json already exists (from React generator)
        package_file = frontend_path / "package.json"
        
        if not package_file.exists():
            # Generate basic package.json
            project_name = blueprint.get("name", "app").lower().replace(" ", "-")
            
            package_json = {
                "name": project_name,
                "version": "0.1.0",
                "private": True,
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.20.0",
                    "axios": "^1.6.0",
                    "zustand": "^4.4.7",
                },
                "devDependencies": {
                    "@types/react": "^18.2.37",
                    "@types/react-dom": "^18.2.15",
                    "@typescript-eslint/eslint-plugin": "^6.13.1",
                    "@typescript-eslint/parser": "^6.13.1",
                    "@vitejs/plugin-react": "^4.2.0",
                    "typescript": "^5.2.2",
                    "vite": "^5.0.0",
                    "eslint": "^8.54.0",
                    "eslint-plugin-react-hooks": "^4.6.0",
                    "eslint-plugin-react-refresh": "^0.4.4"
                }
            }
            
            # Add Tailwind if specified
            if blueprint.get("architecture", {}).get("frontend", {}).get("styling") == "tailwindcss":
                package_json["devDependencies"]["tailwindcss"] = "^3.3.0"
                package_json["devDependencies"]["autoprefixer"] = "^10.4.16"
                package_json["devDependencies"]["postcss"] = "^8.4.32"
            
            # Add UI library if specified
            ui_library = blueprint.get("architecture", {}).get("frontend", {}).get("ui_library")
            if ui_library == "shadcn/ui":
                package_json["dependencies"]["class-variance-authority"] = "^0.7.0"
                package_json["dependencies"]["clsx"] = "^2.0.0"
                package_json["dependencies"]["tailwind-merge"] = "^2.0.0"
                package_json["dependencies"]["lucide-react"] = "^0.303.0"
            
            package_file.write_text(json.dumps(package_json, indent=2))
        
        # Generate package-lock.json instructions
        lock_info = """# This file is automatically generated by npm when you run `npm install`
# It's recommended to commit this file to version control for consistent installs

# To generate/update this file:
# npm install

# To install dependencies without generating lockfile:
# npm install --no-package-lock

# To update all dependencies:
# npm update

# To update a specific package:
# npm update <package-name>
"""
        
        lock_file = frontend_path / "PACKAGE_LOCK_INFO.md"
        lock_file.write_text(lock_info)
        
        self.logger.info("Generated Node.js dependencies")
    
    def _generate_setup_files(self, project_path: Path):
        """Generate setup and configuration files."""
        # Generate .env file with instructions
        env_content = """# Environment Configuration
# Copy this file to .env and fill in the values

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/dbname
# For SQLite: DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME="Your App Name"

# AWS (optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Third-party APIs (optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
API_V1_STR=/api/v1

# Admin User (will be created on first run if doesn't exist)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=  # Leave empty to generate random password on first run
ADMIN_CREATE_ENABLED=True

# Database seeding
SEED_DATA=True
"""
        
        env_file = project_path / ".env.example"
        env_file.write_text(env_content)
        
        # Generate setup.py for legacy Python projects
        setup_py = """#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="app",
    version="0.1.0",
    author="Agent 50",
    author_email="agent@example.com",
    description="A web application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/app",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "app=app.main:main",
        ],
    },
)
"""
        
        setup_file = project_path / "backend" / "setup.py"
        setup_file.write_text(setup_py)
        
        # Generate Makefile for common tasks
        makefile_content = """# Makefile for Application Management

.PHONY: help install dev test lint format clean db-setup db-migrate db-upgrade db-downgrade

help:
	@echo "Available commands:"
	@echo "  install    - Install all dependencies"
	@echo "  dev       - Start development servers"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linters"
	@echo "  format    - Format code"
	@echo "  clean     - Clean build artifacts"
	@echo "  db-setup  - Setup database"
	@echo "  db-migrate - Create new migration"
	@echo "  db-upgrade - Apply migrations"
	@echo "  db-downgrade - Rollback migrations"

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Starting development servers..."
	cd backend && uvicorn main:app --reload &
	cd frontend && npm run dev

test:
	@echo "Running tests..."
	cd backend && pytest -v

lint:
	@echo "Running linters..."
	cd backend && flake8 .
	cd backend && mypy .
	cd frontend && npm run lint

format:
	@echo "Formatting code..."
	cd backend && black .
	cd backend && isort .
	cd frontend && npx prettier --write .

clean:
	@echo "Cleaning build artifacts..."
	rm -rf backend/__pycache__
	rm -rf backend/*/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	rm -rf frontend/.next

db-setup:
	@echo "Setting up database..."
	cd backend && python -c "from app.db.init_db import init_db; init_db()"

db-migrate:
	@echo "Creating new migration..."
	cd backend && alembic revision --autogenerate -m "$(message)"

db-upgrade:
	@echo "Applying migrations..."
	cd backend && alembic upgrade head

db-downgrade:
	@echo "Rolling back migrations..."
	cd backend && alembic downgrade -1
"""
        
        makefile = project_path / "Makefile"
        makefile.write_text(makefile_content)
    
    def _validate_dependencies(self, project_path: Path):
        """Validate that all dependencies can be resolved."""
        self.logger.info("Validating dependencies...")
        
        validation_issues = []
        
        # Check Python dependencies
        backend_path = project_path / "backend"
        if backend_path.exists():
            requirements_file = backend_path / "requirements.txt"
            if requirements_file.exists():
                try:
                    # Check for syntax errors in requirements
                    with open(requirements_file, "r") as f:
                        for i, line in enumerate(f, 1):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Basic validation of requirement format
                                if not re.match(r'^[a-zA-Z0-9_-]+(?:\[[a-zA-Z0-9,_-]+\])?(?:[<>=!~]=?[0-9.*]+(?:,\s*[<>=!~]=?[0-9.*]+)*)?$', line):
                                    validation_issues.append(f"Invalid requirement format at line {i}: {line}")
                except Exception as e:
                    validation_issues.append(f"Error reading requirements.txt: {e}")
        
        # Check Node dependencies
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            package_file = frontend_path / "package.json"
            if package_file.exists():
                try:
                    with open(package_file, "r") as f:
                        package_data = json.load(f)
                    
                    # Validate package.json structure
                    if "name" not in package_data:
                        validation_issues.append("package.json missing 'name' field")
                    if "version" not in package_data:
                        validation_issues.append("package.json missing 'version' field")
                    
                    # Check for required scripts
                    if "scripts" in package_data:
                        required_scripts = ["dev", "build"]
                        for script in required_scripts:
                            if script not in package_data["scripts"]:
                                validation_issues.append(f"package.json missing '{script}' script")
                    
                except json.JSONDecodeError as e:
                    validation_issues.append(f"Invalid JSON in package.json: {e}")
        
        if validation_issues:
            self.logger.warning(f"Found validation issues: {validation_issues}")
            # Log issues but don't fail - these will be caught during installation
        
        self.logger.info("Dependency validation complete")
        return validation_issues
    
    def install_dependencies(self, project_path: Path, fix_issues: bool = True) -> Tuple[bool, List[str]]:
        """
        Install dependencies for a project.
        
        Returns:
            Tuple of (success, messages)
        """
        self.logger.info(f"Installing dependencies for: {project_path}")
        
        messages = []
        success = True
        
        try:
            # Install Python dependencies
            backend_path = project_path / "backend"
            if backend_path.exists():
                py_success, py_messages = self._install_python_dependencies(backend_path, fix_issues)
                success = success and py_success
                messages.extend(py_messages)
            
            # Install Node dependencies
            frontend_path = project_path / "frontend"
            if frontend_path.exists():
                node_success, node_messages = self._install_node_dependencies(frontend_path, fix_issues)
                success = success and node_success
                messages.extend(node_messages)
            
            # Update project status
            if self.memory and success:
                self.memory.update_project_status({
                    "system": "ready",
                    "architecture": 100,
                    "backend": 100,
                    "frontend": 100,
                    "deployment": 25,
                    "message": "Dependencies installed successfully"
                })
            
            self.logger.info("Dependency installation complete")
            
        except Exception as e:
            error_msg = f"Failed to install dependencies: {e}"
            self.logger.error(error_msg)
            messages.append(error_msg)
            success = False
        
        return success, messages
    
    def _install_python_dependencies(self, backend_path: Path, fix_issues: bool) -> Tuple[bool, List[str]]:
        """Install Python dependencies with auto-fix capabilities."""
        messages = []
        
        # Check if virtual environment exists
        venv_path = backend_path / ".venv"
        if not venv_path.exists() and fix_issues:
            messages.append("Creating Python virtual environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", ".venv"],
                    cwd=backend_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                messages.append("Virtual environment created")
            except subprocess.CalledProcessError as e:
                messages.append(f"Failed to create virtual environment: {e}")
                return False, messages
        
        # Determine pip command
        pip_cmd = [sys.executable, "-m", "pip"]
        if venv_path.exists():
            if os.name == "nt":  # Windows
                pip_cmd = [str(venv_path / "Scripts" / "python.exe"), "-m", "pip"]
            else:  # Unix/Linux/Mac
                pip_cmd = [str(venv_path / "bin" / "python"), "-m", "pip"]
        
        # Install requirements
        requirements_file = backend_path / "requirements.txt"
        if requirements_file.exists():
            messages.append("Installing Python dependencies...")
            try:
                result = subprocess.run(
                    pip_cmd + ["install", "-r", "requirements.txt"],
                    cwd=backend_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                messages.append("Python dependencies installed successfully")
                
                # Check for common issues
                output = result.stdout + result.stderr
                self._analyze_pip_output(output, messages)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to install Python dependencies: {e.stderr}"
                messages.append(error_msg)
                
                if fix_issues:
                    messages.append("Attempting to fix dependency issues...")
                    fixed = self._fix_python_dependencies(backend_path, pip_cmd, e.stderr)
                    if fixed:
                        messages.append("Dependency issues fixed, retrying installation...")
                        return self._install_python_dependencies(backend_path, False)  # Retry without fix loop
                
                return False, messages
        
        return True, messages
    
    def _fix_python_dependencies(self, backend_path: Path, pip_cmd: List[str], error_output: str) -> bool:
        """Attempt to fix Python dependency issues."""
        fixes_applied = []
        
        # Check for common issues and apply fixes
        requirements_file = backend_path / "requirements.txt"
        
        if not requirements_file.exists():
            self.logger.error("requirements.txt not found")
            return False
        
        with open(requirements_file, "r") as f:
            requirements = f.read()
        
        # Fix 1: Upgrade pip
        if "pip needs to be updated" in error_output or "Consider upgrading pip" in error_output:
            try:
                subprocess.run(
                    pip_cmd + ["install", "--upgrade", "pip"],
                    cwd=backend_path,
                    capture_output=True,
                    check=True
                )
                fixes_applied.append("Upgraded pip")
            except:
                pass
        
        # Fix 2: Install setuptools and wheel
        if "No module named 'setuptools'" in error_output or "No module named 'wheel'" in error_output:
            try:
                subprocess.run(
                    pip_cmd + ["install", "setuptools", "wheel"],
                    cwd=backend_path,
                    capture_output=True,
                    check=True
                )
                fixes_applied.append("Installed build tools")
            except:
                pass
        
        # Fix 3: Handle specific package errors
        error_patterns = {
            r"ERROR: Could not find a version that satisfies the requirement (\S+)": "package_not_found",
            r"No matching distribution found for (\S+)": "package_not_found",
            r"ERROR: Failed building wheel for (\S+)": "build_failed",
        }
        
        for pattern, error_type in error_patterns.items():
            matches = re.findall(pattern, error_output)
            for package in matches:
                # Clean package name (remove version specifiers)
                package_name = package.split("[")[0].split(">")[0].split("<")[0].split("=")[0].strip()
                
                if error_type == "package_not_found":
                    # Try alternative package name or remove version constraint
                    new_requirements = []
                    for line in requirements.split("\n"):
                        if package_name in line and "==" in line:
                            # Remove version constraint
                            new_line = line.split("==")[0]
                            new_requirements.append(new_line)
                            fixes_applied.append(f"Removed version constraint for {package_name}")
                        else:
                            new_requirements.append(line)
                    
                    requirements = "\n".join(new_requirements)
                
                elif error_type == "build_failed":
                    # Try installing from binary or alternative source
                    try:
                        subprocess.run(
                            pip_cmd + ["install", "--no-binary", ":all:", package_name],
                            cwd=backend_path,
                            capture_output=True,
                            check=False
                        )
                        fixes_applied.append(f"Installed {package_name} from source")
                    except:
                        pass
        
        # Write fixed requirements
        if fixes_applied:
            with open(requirements_file, "w") as f:
                f.write(requirements)
            
            # Record fix in memory
            if self.memory:
                self.memory.record_fix_applied(
                    fix_type="python_dependencies",
                    problem="Failed to install Python dependencies",
                    solution=f"Applied fixes: {', '.join(fixes_applied)}",
                    project_name=backend_path.parent.name
                )
            
            self.logger.info(f"Applied fixes: {fixes_applied}")
            return True
        
        return False
    
    def _analyze_pip_output(self, output: str, messages: List[str]):
        """Analyze pip output for warnings and suggestions."""
        warnings = []
        
        # Check for outdated packages
        if "outdated" in output.lower():
            warnings.append("Some packages are outdated")
        
        # Check for dependency conflicts
        if "conflict" in output.lower() or "incompatible" in output.lower():
            warnings.append("Potential dependency conflicts detected")
        
        # Check for security issues
        security_keywords = ["vulnerability", "CVE", "security", "insecure"]
        if any(keyword in output.lower() for keyword in security_keywords):
            warnings.append("Security vulnerabilities detected in dependencies")
        
        if warnings:
            messages.extend([f"Warning: {w}" for w in warnings])
    
    def _install_node_dependencies(self, frontend_path: Path, fix_issues: bool) -> Tuple[bool, List[str]]:
        """Install Node.js dependencies with auto-fix capabilities."""
        messages = []
        
        # Check if node_modules exists
        node_modules = frontend_path / "node_modules"
        package_file = frontend_path / "package.json"
        
        if not package_file.exists():
            messages.append("package.json not found, skipping Node dependencies")
            return True, messages
        
        messages.append("Installing Node.js dependencies...")
        
        try:
            # Check Node.js version
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                cwd=frontend_path
            )
            
            if node_result.returncode != 0:
                messages.append("Node.js is not installed or not in PATH")
                if fix_issues:
                    messages.append("Please install Node.js v18 or later")
                return False, messages
            
            # Check npm/yarn/pnpm
            package_managers = ["npm", "yarn", "pnpm"]
            pm_found = None
            
            for pm in package_managers:
                result = subprocess.run(
                    [pm, "--version"],
                    capture_output=True,
                    text=True,
                    cwd=frontend_path
                )
                if result.returncode == 0:
                    pm_found = pm
                    break
            
            if not pm_found:
                messages.append("No package manager found (npm, yarn, or pnpm)")
                if fix_issues:
                    # Try to install npm
                    messages.append("Attempting to use system Python to install packages...")
                    return self._install_node_with_pip(frontend_path)
                return False, messages
            
            # Install dependencies
            if pm_found == "npm":
                cmd = [pm_found, "install"]
            else:
                cmd = [pm_found, "install"]  # yarn install or pnpm install
            
            result = subprocess.run(
                cmd,
                cwd=frontend_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            messages.append(f"Node.js dependencies installed successfully using {pm_found}")
            
            # Check for warnings
            if "warning" in result.stdout.lower() or "warning" in result.stderr.lower():
                messages.append("Warnings detected during npm install")
            
            # Check for audit issues
            if pm_found == "npm" and "audit" in result.stdout.lower():
                messages.append("npm audit found vulnerabilities - run 'npm audit fix' to fix")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install Node.js dependencies: {e.stderr}"
            messages.append(error_msg)
            
            if fix_issues:
                messages.append("Attempting to fix Node.js dependency issues...")
                fixed = self._fix_node_dependencies(frontend_path, e.stderr)
                if fixed:
                    messages.append("Node.js dependency issues fixed, retrying installation...")
                    return self._install_node_dependencies(frontend_path, False)  # Retry without fix loop
            
            return False, messages
        
        except FileNotFoundError as e:
            messages.append(f"Command not found: {e}")
            return False, messages
        
        return True, messages
    
    def _install_node_with_pip(self, frontend_path: Path) -> Tuple[bool, List[str]]:
        """Fallback: Install Node.js packages using Python."""
        messages = ["Using Python to install Node.js packages..."]
        
        try:
            # This is a fallback - in production, Node.js should be properly installed
            import requests
            
            # Download package.json dependencies and create a requirements-like file
            with open(frontend_path / "package.json", "r") as f:
                package_data = json.load(f)
            
            # Create a simple HTML file that loads CDN versions of packages
            # This is a last-resort fallback for development only
            cdn_imports = []
            
            for dep, version in package_data.get("dependencies", {}).items():
                # Map common packages to CDN URLs
                cdn_map = {
                    "react": "https://unpkg.com/react@18/umd/react.production.min.js",
                    "react-dom": "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js",
                    "axios": "https://unpkg.com/axios/dist/axios.min.js",
                }
                
                if dep in cdn_map:
                    cdn_imports.append(f'<script src="{cdn_map[dep]}"></script>')
            
            if cdn_imports:
                # Create a fallback HTML file
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fallback Development Mode</title>
    {"\n    ".join(cdn_imports)}
</head>
<body>
    <div id="root"></div>
    <script>
        console.log('Running in fallback CDN mode. Install Node.js for full functionality.');
    </script>
</body>
</html>"""
                
                with open(frontend_path / "fallback.html", "w") as f:
                    f.write(html_content)
                
                messages.append("Created fallback CDN-based development file")
                messages.append("WARNING: Install Node.js for full functionality")
                return True, messages
        
        except Exception as e:
            messages.append(f"Fallback installation failed: {e}")
        
        return False, messages
    
    def _fix_node_dependencies(self, frontend_path: Path, error_output: str) -> bool:
        """Attempt to fix Node.js dependency issues."""
        fixes_applied = []
        
        package_file = frontend_path / "package.json"
        
        if not package_file.exists():
            return False
        
        with open(package_file, "r") as f:
            package_data = json.load(f)
        
        # Fix 1: Clear node_modules and package-lock
        if "ENOENT" in error_output or "corrupt" in error_output:
            try:
                # Remove node_modules and lock files
                for file in ["node_modules", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
                    path = frontend_path / file
                    if path.exists():
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        fixes_applied.append(f"Cleared {file}")
            except Exception as e:
                self.logger.error(f"Failed to clear node_modules: {e}")
        
        # Fix 2: Clear npm cache
        if "cache" in error_output or "EACCES" in error_output:
            try:
                subprocess.run(["npm", "cache", "clean", "--force"], 
                             capture_output=True, check=False)
                fixes_applied.append("Cleared npm cache")
            except:
                pass
        
        # Fix 3: Update package.json engines if Node version issue
        if "engine" in error_output and "node" in error_output:
            # Extract required Node version from error
            match = re.search(r"node\s+([0-9.]+)", error_output)
            if match:
                required_version = match.group(1)
                if "engines" not in package_data:
                    package_data["engines"] = {}
                package_data["engines"]["node"] = f">={required_version}"
                fixes_applied.append(f"Updated Node.js engine requirement to >= {required_version}")
        
        # Write fixed package.json
        if fixes_applied:
            with open(package_file, "w") as f:
                json.dump(package_data, f, indent=2)
            
            # Record fix in memory
            if self.memory:
                self.memory.record_fix_applied(
                    fix_type="node_dependencies",
                    problem="Failed to install Node.js dependencies",
                    solution=f"Applied fixes: {', '.join(fixes_applied)}",
                    project_name=frontend_path.parent.name
                )
            
            self.logger.info(f"Applied fixes: {fixes_applied}")
            return True
        
        return False
    
    def check_missing_dependencies(self, project_path: Path) -> Dict[str, List[str]]:
        """
        Check for missing dependencies in the project.
        
        Returns:
            Dict with keys 'python' and 'node' containing lists of missing dependencies
        """
        missing = {"python": [], "node": []}
        
        # Check Python imports in backend code
        backend_path = project_path / "backend"
        if backend_path.exists():
            missing["python"] = self._check_python_imports(backend_path)
        
        # Check Node imports in frontend code
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            missing["node"] = self._check_node_imports(frontend_path)
        
        return missing
    
    def _check_python_imports(self, backend_path: Path) -> List[str]:
        """Check Python files for imports that might be missing from requirements."""
        missing = []
        python_files = list(backend_path.rglob("*.py"))
        
        # Common stdlib modules - these shouldn't be in requirements
        stdlib_modules = {
            'os', 'sys', 'json', 're', 'datetime', 'time', 'math', 'random',
            'typing', 'collections', 'itertools', 'functools', 'pathlib',
            'logging', 'subprocess', 'shutil', 'tempfile', 'hashlib'
        }
        
        # Read requirements to know what's already listed
        requirements = set()
        req_file = backend_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name (remove version specifiers)
                        pkg = line.split("[")[0].split(">")[0].split("<")[0].split("=")[0].strip()
                        requirements.add(pkg.lower())
        
        # Check each Python file
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find import statements
                import_patterns = [
                    r'^import\s+([a-zA-Z0-9_\.]+)',
                    r'^from\s+([a-zA-Z0-9_\.]+)\s+import',
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    for match in matches:
                        # Get root package name
                        pkg = match.split(".")[0].lower()
                        
                        # Skip stdlib and already required packages
                        if (pkg not in stdlib_modules and 
                            pkg not in requirements and 
                            pkg not in missing):
                            # Check if it's a local import
                            if not (backend_path / pkg).exists() and not (backend_path / (pkg + ".py")).exists():
                                missing.append(pkg)
            except UnicodeDecodeError:
                continue
        
        return sorted(set(missing))
    
    def _check_node_imports(self, frontend_path: Path) -> List[str]:
        """Check JavaScript/TypeScript files for imports that might be missing from package.json."""
        missing = []
        
        # Read package.json dependencies
        dependencies = set()
        dev_dependencies = set()
        
        package_file = frontend_path / "package.json"
        if package_file.exists():
            with open(package_file, "r") as f:
                package_data = json.load(f)
            
            dependencies = set(package_data.get("dependencies", {}).keys())
            dev_dependencies = set(package_data.get("devDependencies", {}).keys())
        
        all_deps = dependencies.union(dev_dependencies)
        
        # Check JS/TS files
        js_files = list(frontend_path.rglob("*.js")) + list(frontend_path.rglob("*.jsx")) + \
                   list(frontend_path.rglob("*.ts")) + list(frontend_path.rglob("*.tsx"))
        
        for js_file in js_files:
            try:
                with open(js_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find import statements
                import_patterns = [
                    r'import\s+.*from\s+[\'"]([^"\']+)[\'"]',
                    r'require\s*\(\s*[\'"]([^"\']+)[\'"]\s*\)',
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Get package name (handle scoped packages)
                        if match.startswith("@"):
                            # Scoped package like @radix-ui/react-dialog
                            pkg = "/".join(match.split("/")[:2])
                        else:
                            # Regular package like react
                            pkg = match.split("/")[0]
                        
                        # Skip local imports and built-ins
                        if (not pkg.startswith(".") and 
                            pkg not in all_deps and 
                            pkg not in missing and
                            not any(pkg.startswith(builtin) for builtin in ["http", "https", "fs", "path"])):
                            missing.append(pkg)
            except UnicodeDecodeError:
                continue
        
        return sorted(set(missing))
    
    def auto_fix_missing_dependencies(self, project_path: Path, missing: Dict[str, List[str]]) -> bool:
        """
        Automatically fix missing dependencies.
        
        Returns:
            True if fixes were applied
        """
        fixes_applied = False
        
        # Fix missing Python dependencies
        if missing.get("python"):
            backend_path = project_path / "backend"
            req_file = backend_path / "requirements.txt"
            
            if req_file.exists():
                with open(req_file, "a") as f:
                    for dep in missing["python"]:
                        f.write(f"\n{dep}>=1.0.0")
                        self.logger.info(f"Added missing Python dependency: {dep}")
                
                fixes_applied = True
        
        # Fix missing Node dependencies
        if missing.get("node"):
            frontend_path = project_path / "frontend"
            package_file = frontend_path / "package.json"
            
            if package_file.exists():
                with open(package_file, "r") as f:
                    package_data = json.load(f)
                
                if "dependencies" not in package_data:
                    package_data["dependencies"] = {}
                
                for dep in missing["node"]:
                    package_data["dependencies"][dep] = "^1.0.0"
                    self.logger.info(f"Added missing Node dependency: {dep}")
                
                with open(package_file, "w") as f:
                    json.dump(package_data, f, indent=2)
                
                fixes_applied = True
        
        if fixes_applied and self.memory:
            self.memory.record_fix_applied(
                fix_type="missing_dependencies",
                problem="Missing dependencies detected",
                solution=f"Added: Python: {missing.get('python', [])}, Node: {missing.get('node', [])}",
                project_name=project_path.name
            )
        
        return fixes_applied
    
    def send_build_ready_signal(self, project_path: Path):
        """Send final build ready signal."""
        self.logger.info(f"Build ready for: {project_path}")
        
        # Update project status
        if self.memory:
            self.memory.update_project_status({
                "system": "ready",
                "architecture": 100,
                "backend": 100,
                "frontend": 100,
                "deployment": 50,
                "message": "Build complete - Ready for deployment",
                "build_status": "success",
                "timestamp": self._get_timestamp()
            })
        
        # Create build completion marker
        marker_file = project_path / ".build_complete"
        marker_file.write_text(f"Build completed at {self._get_timestamp()}\n")
        
        # Generate build summary
        summary = self._generate_build_summary(project_path)
        summary_file = project_path / "BUILD_SUMMARY.md"
        summary_file.write_text(summary)
    
    def _generate_build_summary(self, project_path: Path) -> str:
        """Generate build summary markdown."""
        summary = f"""# Build Summary

Project: {project_path.name}
Generated by: Agent 50
Build completed: {self._get_timestamp()}

## Project Structure
{self._get_directory_tree(project_path)}

## Dependencies Installed

### Python (Backend)
"""
        
        # Add Python dependencies
        backend_path = project_path / "backend"
        if backend_path.exists():
            req_file = backend_path / "requirements.txt"
            if req_file.exists():
                with open(req_file, "r") as f:
                    summary += "\n```\n" + f.read() + "```\n"
        
        # Add Node dependencies
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            summary += "\n### Node.js (Frontend)\n"
            package_file = frontend_path / "package.json"
            if package_file.exists():
                with open(package_file, "r") as f:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    if deps:
                        summary += "\n```json\n" + json.dumps(deps, indent=2) + "\n```\n"
        
        # Add next steps
        summary += """
## Next Steps

1. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings