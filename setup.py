from setuptools import setup, find_packages

setup(
    name="headhunter",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "playwright",
        "sqlalchemy",
        "psycopg2-binary",
        "python-dotenv",
        "beautifulsoup4",
    ],
    python_requires=">=3.8",
) 