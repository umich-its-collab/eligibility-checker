from setuptools import setup

setup(
      name='eligibility-checker',
      version='0.5',
      description='Standardized eligibility checking for U-M ITS Collaboration Services',
      url='https://github.com/umich-its-collab/eligibility-checker',
      author='University of Michigan ITS Collaboration Services',
      author_email='4help@umich.edu',
      packages=['eligibility_checker'],
      install_requires=[
            'mcommunity @ git+https://github.com/umich-its-collab/mcommunity-tools.git@v0.5#egg=mcommunity'
      ]
)
