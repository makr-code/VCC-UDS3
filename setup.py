from setuptools import setup, find_packages
import os
import sys

# Add current directory to path to import version
sys.path.insert(0, os.path.dirname(__file__))

def read_file(filename):
    """Read a file and return its contents"""
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Get long description from README
long_description = read_file('docs/DEVELOPER_HOWTO.md') if os.path.exists('docs/DEVELOPER_HOWTO.md') else read_file('README.md') if os.path.exists('README.md') else ""

setup(
    name="uds3",
    version="1.5.0",  # Sync with pyproject.toml
    description="UDS3 - Unified Database Strategy v3: Enterprise Multi-Database Distribution System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Martin Krüger",
    author_email="ma.krueger@outlook.com", 
    url="https://github.com/makr-code/VCC-UDS3",
    license="MIT",
    project_urls={
        "Documentation": "https://github.com/makr-code/VCC-UDS3/blob/main/README.md",
        "Source": "https://github.com/makr-code/VCC-UDS3",
        "Issues": "https://github.com/makr-code/VCC-UDS3/issues",
        "Changelog": "https://github.com/makr-code/VCC-UDS3/blob/main/docs/CHANGELOG.md",
        "Security": "https://github.com/makr-code/VCC-UDS3/blob/main/docs/SECURITY.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    package_data={
        "uds3": ["*.json", "*.yaml", "*.yml"],
        "api": ["*.json", "geo_config.json"],
        "docs": ["*.md"],
    },
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        # Core Database Adapters
        "psycopg2>=2.9.0",          # PostgreSQL (with batch operations)
        "neo4j>=5.0.0",              # Neo4j Graph Database (with batch operations)
        "CouchDB>=1.2",              # CouchDB Document Store (with batch operations)
        
        # Vector & Embedding Support
        "requests>=2.28.0",          # ChromaDB Remote HTTP Client
        "sentence-transformers>=2.2.0",  # Real embeddings (optional)
        
        # Data Processing
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        
        # Utilities
        "python-dotenv>=0.19.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "embeddings": [
            "torch>=1.13.0",         # For GPU-accelerated embeddings
            "transformers>=4.20.0",
        ],
        "monitoring": [
            "prometheus-client>=0.14.0",
            "grafana-api>=1.0.3",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "uds3=uds3:main",  # Main UDS3 CLI entry point
            "uds3-manager=api.manager:main",  # API Manager CLI
        ],
    },
    zip_safe=False,  # Package contains data files
    platforms=["any"],
)
