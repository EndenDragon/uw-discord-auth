#!/usr/bin/env python3

## This script contains the CGI configuration required to serve up your Flask
## web application from itself. Used with the provided .htaccess file,
## you can serve up your site from a directory.
## It works by making your installed PIP packages avaliable from
## a given folder and then importing your project so that it may be executed.

## Making installed PIP packages avaliable to be imported in Python
# PIP Packages directory; ./pypackages means the folder called pypackages located at
# the current directory as application.cgi
PIP_PACKAGES_DIR = "./pypackages" ### CHANGE THIS!
import sys
sys.path.insert(0, PIP_PACKAGES_DIR)

## Import your Flask site
# Change this line to point to the Flask's app object.
# from flaskapp import app -> means read flaskapp.py
# and get the app object.
from uwdiscord.app import app ### CHANGE THIS!

## Import CGIHandler object that will run your Flask site.
## Flask is written so that it follows Python Web Server
## Gateway Interface (WSGI). Because of this, many server
## software that can interpret Python may run any Flask site.
## Python's built in wsgiref package allow running WSGI web applications
## in a CGI environment. (i.e. UW student web publishing can run CGI scripts)
from wsgiref.handlers import CGIHandler
CGIHandler().run(app)
