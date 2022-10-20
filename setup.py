from setuptools import setup

setup(
  name='veracode-pov-automation-tool',
  version='0.0.1',
  author='Vincent Deng',
  author_email='vsdeng@veracode.com',
  python_requires='>=3.6',
  py_modules=['pov', 'constant', 'credentials_commands', 'application_commands',
              'user_commands'],
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
