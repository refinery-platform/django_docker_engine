import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django_docker_engine',
    version='0.0.3',
    install_requires=[
        'django',
        'docker==2.1.0',
        'django-http-proxy',
        'boto3',
        'troposphere',
        'paramiko',
        'timeout-decorator'
    ],
    packages=find_packages(exclude=['*_demo']),
    include_package_data=True,
    license='MIT License',  # example license
    description='Django app that manages the creation of, ' +
                'and proxies requests to, Docker containers',
    long_description=README,
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
