import os
import re
import sys
from os.path import abspath, dirname, join, normpath

import yaml
from setuptools import find_packages, setup

with open(join(dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(normpath(join(abspath(__file__), os.pardir)))

travis = yaml.load(open('.travis.yml').read())
django_versions = [
    re.search(r'DJANGO_VERSION.*(\d+\.\d+)\.', v).group(1)
    for v in travis['env']['matrix']
]
assert len(django_versions) > 0
django_classifiers = ['Framework :: Django :: ' + v for v in django_versions]

version = open(join('django_docker_engine', 'VERSION.txt')).read().strip()

setup(
    name='django_docker_engine',
    version=version,
    install_requires=[
        # Latest django does not work with python2.
        'django' if sys.version_info[0] > 2 else 'django<2.0',
        'docker>=2.3.0',  # nano_cpus available with this release
        'django-revproxy'
    ],
    packages=find_packages(exclude=['demo_*', 'tests']),
    include_package_data=True,
    license='MIT License',
    description='Django app that manages the creation of, ' +
                'and proxies requests to, Docker containers',
    url='https://github.com/refinery-platform/django_docker_engine/',
    author='Chuck McCallum',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django'] + django_classifiers,
    zip_safe=False
    # TODO: This fixes "ValueError: bad marshal data (unknown type code)"
    # ... but I don't understand why it broke, or whether this is a good fix.
)
