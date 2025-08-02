"""
Setup script for Scholarly Clone.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="scholarly-clone",
    version="1.0.0",
    author="AI Engineer",
    author_email="ai@example.com",
    description="A research-focused web scraping and summarization platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/scholarly-clone",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Researchers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "scholarly-clone=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "scholarly_clone": [
            "frontend/*.html",
            "frontend/*.css",
            "frontend/*.js",
        ],
    },
    keywords="research web-scraping ai langchain crawl4ai scholarly",
    project_urls={
        "Bug Reports": "https://github.com/your-username/scholarly-clone/issues",
        "Source": "https://github.com/your-username/scholarly-clone",
        "Documentation": "https://github.com/your-username/scholarly-clone/blob/main/README.md",
    },
)