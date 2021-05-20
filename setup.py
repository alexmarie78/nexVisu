
from setuptools import setup, find_packages

__author__ = ["Alexandre Marie"]
__date__ = "05/11/2020"
__license__ = "AGPL"

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="nexVisu",
    version="1.0",
    author=__author__,
    author_email="alexandre.marie@synchrotron-soleil.fr",
    description="package for nexus data visualisation and correction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexmarie78/nexVisu",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: AGPL License",
        "Operating System :: OS Independent",
        ],
    packages= find_packages(),
    python_requires='~=3.6',
    license="AGPLv3",
    )
