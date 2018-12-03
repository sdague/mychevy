#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests',
    'click>=6',
    # TODO: put package requirements here
]

setup_requirements = [
    'pytest-runner',
    # TODO(sdague): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    # TODO: put package test requirements here
]

setup(
    name='mychevy',
    version='1.0.0',
    description="Python interface to My Chevy website via Selenium",
    long_description=readme + '\n\n' + history,
    author="Sean Dague",
    author_email='sean@dague.net',
    url='https://github.com/sdague/mychevy',
    packages=find_packages(include=['mychevy']),
    entry_points={
        'console_scripts': [
            'mychevy=mychevy.cli:main',
            'mychevy-debug=mychevy.debug:main',
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='mychevy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
