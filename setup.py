"""
Automotive Price Monitor Setup
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="automotive-price-monitor",
    version="1.0.0",
    author="Automotive Price Monitor Team",
    author_email="admin@lavazembazaar.com",
    description="A comprehensive system for monitoring automotive parts prices across Iranian e-commerce sites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/automotive-price-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
            "isort>=5.0",
        ],
        "prod": [
            "gunicorn>=21.0",
            "supervisor>=4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "automotive-scraper=scripts.run_scraper:main",
            "automotive-updater=scripts.update_prices:main",
            "automotive-dashboard=run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.json", "*.html", "*.css", "*.js"],
    },
)
