# @rebootstr

# states
BASE_STATE = "BASE_STATE"
ADMIN_CODE = "ADMIN_CODE"
SILENT_BIG_SENDING = "SILENT_MESSAGE"
NORMAL_BIG_SENDING = "NORMAL_MESSAGE"
# params
CODE = "code"


def baseState():
    return BASE_STATE


def adminCode(code: int):
    return f"{ADMIN_CODE}?{CODE}={code}"


def silentBigSending():
    return SILENT_BIG_SENDING


def normalBigSending():
    return NORMAL_BIG_SENDING


def getParams(state: str):
    params = {}
    for param in state.split("?")[1:]:
        name, value = param.split("=")
        params[name] = value
    return params
