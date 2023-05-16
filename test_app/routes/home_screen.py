from routes import flask_app as app
from flask import render_template, request

print("main.py was successfully called")
print("this is the new main.py")

import sys

print("python version is: " + sys.version)
print("python path is", sys.path)

import os

print("imported os")
print("contents of this dir", os.listdir("./"))


print("imported flask etc")

from constants import RUNNING_ON_ANDROID
from tools import (
    vibrate_with_pyjnius,
    get_android_python_activity,
    set_device_orientation,
    setup_lifecycle_callbacks,
    ShowToast,
)


setup_lifecycle_callbacks()
service_running = False
TESTS_TO_PERFORM = dict()
NON_ANDROID_DEVICE_MSG = "Not running from Android device"


def get_test_service():
    from jnius import autoclass

    return autoclass("org.test.unit_tests_app.ServiceP4a_test_service")


def start_service():
    global service_running
    activity = get_android_python_activity()
    test_service = get_test_service()
    test_service.start(activity, "Some argument")
    service_running = True


def stop_service():
    global service_running
    activity = get_android_python_activity()
    test_service = get_test_service()
    test_service.stop(activity)
    service_running = False


@app.route("/")
def index():
    return render_template(
        "index.html",
        platform="Android" if RUNNING_ON_ANDROID else "Desktop",
        show_add={"is_show": True},
        navigation_btns={
            "Cuttings": "cutting",
            "System Info": "",
            "Service": "",
            "Configuration": "",
        },
    )


@app.route("/page2")
def page2():
    print(RUNNING_ON_ANDROID)
    return render_template(
        "page2.html",
        platform="Android" if RUNNING_ON_ANDROID else "Desktop",
    )


@app.route("/loadUrl")
def loadUrl():
    if not RUNNING_ON_ANDROID:
        print(NON_ANDROID_DEVICE_MSG, "...cancelled loadUrl.")
        return NON_ANDROID_DEVICE_MSG
    args = request.args
    if "url" not in args:
        print("ERROR: asked to open an url but without url argument")
    print("asked to open url", args["url"])
    activity = get_android_python_activity()
    activity.loadUrl(args["url"])
    return ("", 204)


@app.route("/vibrate")
def vibrate():
    if not RUNNING_ON_ANDROID:
        print(NON_ANDROID_DEVICE_MSG, "...cancelled vibrate.")
        return NON_ANDROID_DEVICE_MSG

    args = request.args
    if "time" not in args:
        print("ERROR: asked to vibrate but without time argument")
    print("asked to vibrate", args["time"])
    vibrate_with_pyjnius(int(float(args["time"]) * 1000))
    return ("", 204)


@app.route("/orientation")
def orientation():
    if not RUNNING_ON_ANDROID:
        print(NON_ANDROID_DEVICE_MSG, "...cancelled orientation.")
        return NON_ANDROID_DEVICE_MSG
    args = request.args
    if "dir" not in args:
        print("ERROR: asked to orient but no dir specified")
        return "No direction specified "
    direction = args["dir"]
    set_device_orientation(direction)
    return ("", 204)


@app.route("/service")
def service():
    if not RUNNING_ON_ANDROID:
        print(NON_ANDROID_DEVICE_MSG, "...cancelled service.")
        return (NON_ANDROID_DEVICE_MSG, 400)
    args = request.args
    if "action" not in args:
        print("ERROR: asked to manage service but no action specified")
        return ("No action specified", 400)

    action = args["action"]
    if action == "start":
        start_service()
    else:
        stop_service()
    return ("", 204)


import cv2 as cv
from threading import Thread
import numpy as np


@app.route("/opencamera")
def open_camera():
    from kvdroid.jclass.android.graphics import Color
    from kvdroid.tools.notification import create_notification
    from kvdroid.tools import get_resource

    create_notification(
        small_icon=get_resource("drawable").ico_nocenstore,  # app icon
        channel_id="1",
        title="You have a message",
        text="hi, just wanted to check on you",
        ids=1,
        channel_name=f"ch1",
        large_icon="assets/image.png",
        expandable=True,
        small_icon_color=Color().rgb(
            0x00, 0xC8, 0x53
        ),  # 0x00 0xC8 0x53 is same as 00C853
        big_picture="assets/image.png",
    )


@app.route("/showtoast")
def show_toast():
    return {"message": "success"}
