from setuptools import setup, find_packages

setup(
    name="polly-ide",
    version="2.1.0",
    description="Polly - Advanced AI Coding Assistant CLI based on Pollinations.ai",
    author="Your Name",
    
    # Автоматически находит папку 'polly', если в ней есть __init__.py
    packages=find_packages(),
    
    # Зависимости, которые установятся сами
    install_requires=[
        "requests",
        "rich",
    ],
    
    # Создание команды 'polly' в терминале
    entry_points={
        "console_scripts": [
            "polly=polly.main:main",
        ],
    },
    
    # Дополнительные настройки
    python_requires=">=3.8",
    include_package_data=True,
)
