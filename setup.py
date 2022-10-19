from setuptools import setup

setup(
  name='veracode-pov',
  version='0.1',
  py_modules=['pov'],
  install_requires=[
    'Click',
    'requests',
    'veracode-api-signing'
  ],
  entry_points={
    'console_scripts': [
      'pov=pov:main'
    ]
  }
)
