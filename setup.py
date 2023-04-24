from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# get the dependencies and installs
# with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
#     all_reqs = f.read().split('\n')

# install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
# dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name="egi-check-in-validator",
    author="nikosev",
    author_email="nikos.ev@hotmail.com",
    version="0.1.0",
    license="ASL 2.0",
    url="https://github.com/rciam/check-in-validator-plugin",
    packages=find_packages(),
    scripts=["egi-check-in-validator.py"],
    zip_safe=False,
    # install_requires=install_requires,
    # dependency_links=dependency_links,
    description="A plugin for checking if an Access Token issued by EGI Check-in is valid. This plugin can be used by HTCondor-CE and ARC-CE",
    long_description=long_description,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
    ],
)
