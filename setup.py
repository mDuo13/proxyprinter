"""setuptools based setup module"""

from setuptools import setup

# Convert the markdown readme to ReST using Pandoc
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = open('README.md').read()

setup(
    name='proxyprinter',
    version='0.3.0',
    description='Generate card game mockups from .ods spreadsheets',
    long_description=long_description,
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
        'Programming Language :: Python :: 3.4',
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
    },
    install_requires=[
        'pyexcel-ods3',
    ],
    package_data={
        '': ["proxyprinter.css"],
    }
)
