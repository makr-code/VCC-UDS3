from setuptools import setup, find_packages
from glob import glob

# UDS3 als Package mit allen Submodulen
py_modules = [p[:-3] for p in glob("*.py") if p.endswith(".py") and p not in ["setup.py", "conftest.py"]]

setup(
    name="uds3",
    version="1.0.0",
    description="UDS3 Multi-Database Distribution System",
    packages=find_packages(where="."),
    py_modules=py_modules,
    package_dir={"": "."},
    include_package_data=True,
    python_requires=">=3.10",
)
