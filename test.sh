#!/bin/bash

echo $(cat .env | grep "SUBNET" | sed "s/SUBNET=//")
