import os
from os.path import (join, normpath, dirname, abspath)
from setuptools import find_packages, setup

with open(join(dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(normpath(join(abspath(__file__), os.pardir)))

setup(
    name='django_docker_engine',
    version=open(join(
        dirname(__file__), 'django_docker_engine', 'VERSION.txt'
    )).read().strip(),
    install_requires=[
        'django',
        'docker==2.1.0',
        'django-http-proxy',
        'requests'
    ],
    packages=find_packages(exclude=['*_demo']),
    include_package_data=True,
    license='MIT License',
    description='Django app that manages the creation of, ' +
                'and proxies requests to, Docker containers',
    url='https://github.com/refinery-platform/django_docker_engine/',
    author='Chuck McCallum',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
