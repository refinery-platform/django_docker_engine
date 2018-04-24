import os
import re
import sys
from os.path import abspath, dirname, join, normpath

# isort has different behavior for different versions of python here.
import yaml  # isort:skip
from setuptools import find_packages, setup  # isort:skip

with open(join(dirname(__file__), 'README.md')) as f:
    readme_md = f.read()

# allow setup.py to be run from any path
os.chdir(normpath(join(abspath(__file__), os.pardir)))

version = open(join('django_docker_engine', 'VERSION.txt')).read().strip()
travis = yaml.load(open('.travis.yml').read())

python_classifiers = ['Programming Language :: Python :: {}'.format(v)
                      for v in travis['python']]
assert len(python_classifiers) > 0

django_versions = [
    re.search(r'DJANGO_VERSION.*(\d+\.\d+)\.', v).group(1)
    for v in travis['env']['matrix']
]
django_classifiers = ['Framework :: Django :: {}'.format(v)
                      for v in django_versions]
assert len(django_classifiers) > 0

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
    long_description=readme_md,
    long_description_content_type='text/markdown',
    url='https://github.com/refinery-platform/django_docker_engine/',
    author='Chuck McCallum',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'] + python_classifiers + [
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django'] + django_classifiers,
    zip_safe=False
    # TODO: This fixes "ValueError: bad marshal data (unknown type code)"
    # ... but I don't understand why it broke, or whether this is a good fix.
)
