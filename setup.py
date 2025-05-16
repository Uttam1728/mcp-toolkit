from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-toolkit",
    version="0.1.0",
    author="",
    author_email="",
    description="A toolkit for interacting with Model-Controller-Persistence (MCP) servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-toolkit",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.8.0",
        "pydantic>=2.0.0",
        "fastapi>=0.95.0",
        "sqlalchemy>=1.4.0",
        "httpx>=0.23.0",
        "asyncio>=3.4.3",
        "openai>=1.0.0",
        "anthropic>=0.3.0",
    ],
)
