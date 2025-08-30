#!/bin/bash

isort app/
black app/
flake8 app/