from setuptools import setup, find_packages

setup(
    name="clickup-api-lib",  
    version="0.1.1",  
    packages=find_packages(),
    install_requires=[
        "requests>=2.0.0",
    ],
    description="Library for interacting with the ClickUp API",
    author="Patryk Skibniewski",
    author_email="patrykski07@gmail.com",
    url="https://github.com/RyKaT07/clickup-api-lib.git",
    python_requires=">=3.7"
)
