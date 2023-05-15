from os import environ

RUNNING_ON_ANDROID="ANDROID" if "ANDROID_APP_PATH" in environ else "IOS"
