#!/usr/bin/env python

from setuptools import setup, find_packages, findall

setup(name='EasyUCS',
      version='0.9.4',
      description='A toolbox to help deploy and manage Cisco UCS devices',
      author='Vincent Esposito',
      author_email='vesposit@cisco.com',
      url='https://github.com/vesposito/easyucs',
      packages=find_packages(),
      package_data={
          'easyucs': ['static/**/*', 'templates/**/*'],
          },
      install_requires=[
          'paramiko >= 2.6.0',
          'imcsdk >= 0.9.7',
          'jsonschema >= 3.1.1',
          'python-docx >= 0.8.10',
          'requests >= 2.22.0',
          'ucsmsdk >= 0.9.8',
          'ucscsdk >= 0.9.0.1',
          'matplotlib >= 3.1.1',
          'networkx >= 2.4',
          'Pillow >= 6.2.1',
          'netaddr >= 0.7.19',
          'pyyaml >= 5.1.2',
          'packaging >= 19.0',
          'Flask >= 1.1.1',
          'scipy >= 1.3.1',
          ],
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
          ],
      )
