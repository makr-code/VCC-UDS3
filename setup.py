from setuptools import setup, find_packages
from glob import glob

# UDS3 als Package mit allen Submodulen
py_modules = [p[:-3] for p in glob("*.py") if p.endswith(".py") and p not in ["setup.py", "conftest.py"]]

setup(
    name="uds3",
    version="1.0.0",
    description="UDS3 - Unified Data Strategy 3.0: Polyglot Persistence with Batch Operations",
    author="UDS3 Team",
    author_email="uds3@covina.local",
    url="https://github.com/makr-code/VCC-Covina",
    packages=find_packages(where="."),
    py_modules=py_modules,
    package_dir={"": "."},
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "uds3=uds3.cli:main",  # Optional CLI tool
        ],
    },
)
