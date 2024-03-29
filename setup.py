# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pcooja',
    version='0.1.0',
    description='Python Wrapper for Cooja Simulator',
    long_description=readme,
    author='Jeremy Dubrulle',
    author_email='jeremy.dubrulle@umons.ac.be',
    url='https://github.com/jeremydub/pcooja',
    license=license,
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'docs'))
)

