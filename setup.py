from setuptools import setup
from os.path import join, dirname
import sys

with open(join(dirname(__file__), 'Claypigeon', 'VERSION')) as file:
    version = file.read().strip()

setup(
    name = 'Claypigeon',
    version = version,
    url = 'https://github.com/openaddresses/claypigeonfs',
    author = 'Michal Migurski',
    author_email = 'mike-pypi@teczno.com',
    description = 'FUSE filesystem for remote ranged HTTP files.',
    packages = ['Claypigeon'],
    entry_points = dict(
        console_scripts = [
            'claypigeon-mount = Claypigeon.filesystem:main',
        ]
    ),
    package_data = {'Claypigeon': ['VERSION']},
    test_suite = 'Claypigeon.tests',
    install_requires = [
        'llfuse == 1.1.1',
        'requests == 2.12.4',
        ]
)
