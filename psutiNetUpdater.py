import logging
import time
from threading import Thread, Lock

from HTTPServer import HTTPServer

file_log = logging.FileHandler("log.log")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("").addHandler(file_log)

sender_period = 60

alive_check_period = sender_period / 2
dead_check_period = sender_period / 4

ALLOWED_SKIPS = 2
SILENT_TIME_MINUTES = 5

STATUS_ALIVE = "Интернет ожил во имя святого Лемжина (спустя {0} секунд)"
STATUS_DEAD = "Инет упал, опять.."

_is_internet_alive = True
last_update_time = time.time()
deadTime = 0
lock = Lock()


def t_updater(sendStatusFunc):
    while True:
        try:
            check_period = get_check_period()
            time.sleep(check_period)
            lock.acquire()
            lut = last_update_time
            lock.release()
            time_passed = time.time() - lut
            if time_passed > get_allowed_skips() * sender_period:
                internet_status_dead(lut, sendStatusFunc)
            else:
                internet_status_alive(sendStatusFunc)
        except Exception as e:
            logging.info(e)
            sendStatusFunc("Проблема, админ чекни лог пж")


def get_allowed_skips():
    return ALLOWED_SKIPS + 2  # VERY DIFFICULT LOGIC, JUST TRUST ME


def get_check_period() -> float:
    if _is_internet_alive:
        return alive_check_period
    else:
        return dead_check_period


def internet_status_dead(lastUpdateTime, sendStatusFunc):
    global _is_internet_alive, deadTime
    if not _is_internet_alive:  # already dead - skip
        return

    _is_internet_alive = False
    send_silent_status(STATUS_DEAD, sendStatusFunc)
    deadTime = lastUpdateTime


def internet_status_alive(sendStatusFunc):
    global _is_internet_alive
    if _is_internet_alive:  # already alive - skip
        return

    _is_internet_alive = True
    timePassed = time.time() - deadTime
    status = STATUS_ALIVE.format(int(timePassed))
    if timePassed > SILENT_TIME_MINUTES * 60:
        sendStatusFunc(status)
    else:
        send_silent_status(status, sendStatusFunc)


def send_silent_status(status: str, sendStatusFunc):
    sendStatusFunc(status, silent=1)


def no_slash(bytes):
    return str(bytes).replace("\\n", "\n").replace("\\r", "\r")[2:-1]


def t_listener(onAliveReceived):
    global last_update_time
    server = HTTPServer()

    while True:
        try:
            response, address = server.get_bytes()
        except Exception as e:
            logging.info(f"something wrong with connection: {e}")
            continue
        if response == b"INTERNET IS ALIVE":
            lock.acquire()
            last_update_time = time.time()
            logging.info("alive received from " + str(address))
            onAliveReceived()
            lock.release()
        else:
            logging.info(f"received unknown bytes from {address}\n{no_slash(response)}")


def run(sendStatusFunc, onAliveReceived):
    updaterThread = Thread(target=t_updater, args=(sendStatusFunc,), daemon=True)
    updaterThread.start()
    listenerThread = Thread(target=t_listener, args=(onAliveReceived,), daemon=True)
    listenerThread.start()



