from setuptools import setup, find_packages

setup(
    name="polly-ide",
    version="2.3.0", # <-- BUMP VERSION
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "polly=polly.main:main",
        ],
    },
)
