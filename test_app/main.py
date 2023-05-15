import sys
import unittest
from routes import flask_app
from os import curdir
from os.path import isfile, realpath
from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
import asyncio

print("Imported unittest")

sys.path.append("./")

# read `app_requirements.txt` and find out which tests to perform
tests_to_perform = {}
requirements = None
if isfile("app_requirements.txt"):
    with open("app_requirements.txt", "r") as requirements_file:
        requirements = set(requirements_file.read().splitlines())
if not requirements:
    # we will test a basic set of recipes
    requirements = {"sqlite3", "libffi", "openssl", "pyjnius", "flask"}
print("App requirements are: ", requirements)

for recipe in requirements:
    test_name = "tests.test_requirements.{recipe}TestCase".format(
        recipe=recipe.capitalize()
    )
import os

if __name__ == "__main__":
    if "flask" in requirements:
        print(f"inside Test to perform : {tests_to_perform}")

        print("Current directory is ", realpath(curdir))
        flask_debug = not realpath(curdir).startswith("/data")

        # Flask is run non-threaded since it tries to resolve app classes
        # through pyjnius from request handlers. That doesn't work since the
        # JNI ends up using the Java system class loader in new native
        # threads.
        #
        # https://github.com/kivy/python-for-android/issues/2533
        statechart = import_from_yaml(filepath=f"{os.curdir}/iotnode/statecharts/main.yml")
        interpreter = Interpreter(statechart)

        loop = asyncio.get_event_loop()
        print(f"CURRENT EVENT LOOP  : {loop}")
        flask_app.run(threaded=False, debug=flask_debug)
