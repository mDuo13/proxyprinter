#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""setuptools based setup module"""

from setuptools import setup

long_description = open('README.md').read()

setup(
    name='proxyprinter',
    version='0.4.0-a29',
    description='Generate card game mockups from .ods spreadsheets',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/mduo13/proxyprinter',
    author='Rome Reginelli',
    author_email='mduo13@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Topic :: Utilities',
        'Topic :: Games/Entertainment :: Board Games',
    ],
    keywords='games mockups proxying design',
    packages=[
        'proxyprinter',
    ],
    entry_points={
        'console_scripts': [
            'proxyprinter = proxyprinter.proxyprinter:main',
        ],
        'gui_scripts': [
            'proxyprintergui = proxyprinter.gui:main',
        ]
    },
    install_requires=[
        'pyexcel-ods3',
    ],
    package_data={
        '': ["proxyprinter.css"],
        '': ["zipcode.html"],
    }
)
