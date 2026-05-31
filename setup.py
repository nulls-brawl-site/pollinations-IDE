from setuptools import setup, find_packages

setup(
    name="pollinations-cli",
    version="3.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "rich",
        "typing_extensions",
    ],
    entry_points={
        "console_scripts": [
            "polly=polly.main:main",
            "pollinations=polly.main:main",
        ],
    },
)
