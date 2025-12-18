from setuptools import setup

setup(
      name='eligibility-checker',
      version='0.11',
      description='Standardized eligibility checking for U-M ITS Collaboration Services',
      url='https://github.com/umich-its-collab/eligibility-checker',
      author='Maggie Davidson',
      author_email='jmaggie@umich.edu',
      packages=['eligibility_checker'],
      install_requires=[
            'mcommunity @ git+https://github.com/umich-its-collab/mcommunity-tools.git@v.10#egg=mcommunity'
      ]
)
