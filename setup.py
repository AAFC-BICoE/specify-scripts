from distutils.core import setup
import setuptools

setup(
    name="specifycleaning",
    version="0.1.0",
    author="Brooke Clouston",
    author_email="brooke.clouston@canada.ca",
    packages=setuptools.find_packages(),
    url="https://github.com/AAFC-BICoE/specify-scripts",
    license="LICENSE",
    description="A collection of scripts to be used with data from a Specify 6 database contained "
                "in a MySQL schema for data cleaning and report creation.",
    long_description=open("README.md").read(),
    install_requires=["anytree==2.4.3",
                      "PyMySQL==0.8.1",
                      "python_Levenshtein==0.12.0",
                      "Pillow==5.2.0"
    ],

)