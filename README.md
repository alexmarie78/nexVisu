# Nexus Visualisation Correction and Processing - NVCP
The goal is to visualize raw data, compute (or load) and apply geometrical corrections on it. Then, it is also possible 
to generate diffraction diagram from corrected data, and at last fit the data. All this steps are processed along one 
detector, that is first chosen by the user. This software is one of my main project developed during my apprenticeship 
at SOLEIL Syncrhotron.


## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing 
purposes. See deployment for notes on how to deploy the project on a live system.
You can download the repository at : https://github.com/alexmarie78/nexVisu

You could also run the command : 
```
git clone https://github.com/alexmarie78/nexVisu.git
```


## Prerequisites
What things you need to install the software and how to install them

To run this project, you need to install python3 by running the command :

```
pip install python3
```


## Installing
A step by step series of examples that tell you how to get a development env running

After downloading the package and having python3 ready on your machine, run the following :

```
python -m pip install -r /path_to_thepackage/requirements.txt
```

When pip had finished that, you are ready to go, the package and its dependencies will be installed.

After the installation, you only need to run the following command to test the software :
```
python3 /path_to_the_package/src/nexVisu_start.py
```

## Running the tests
Tests do not exist right now as the software is still being developed.

## Deployment
Idem as tests.

## Tutorials
There is a french tutorial on how to use the software, available here : \
https://github.com/alexmarie78/nexVisu/src/doc/tutorial.pdf

## Built With
Python - The interpreted language \
PyQt5 - Module used for the graphical user interface (GUI), that links python and Qt5 \
Silx - Module used for the mathematical part of the GUI.
## Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning
We use git for versioning. For the versions available, see the tags on this repository.

## Authors
Alexandre MARIE - Initial work - NVCP \
See also the list of contributors who participated in this project.

## License
This project is licensed under the AGPL-3.0 License - see the LICENSE.md file for details

## Acknowledgments
Hat tip to silx-kit and their developers.
