import logging
import time
from threading import Thread, Lock

import properties
from HTTPServer import HTTPServer
from vk import VK

file_log = logging.FileHandler("log.log")
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)
logging.getLogger("").addHandler(file_log)


def t_updater():
    while True:
        try:
            check_period = get_check_period()
            time.sleep(check_period)
            lock.acquire()
            lut = last_update_time
            lock.release()
            time_passed = time.time() - lut
            if time_passed > get_allowed_skips() * sender_period:
                internet_status_dead()
            else:
                internet_status_alive(time_passed)
        except Exception as e:
            logging.info(e)
            send_status("Поток умер изза эксепшена (см логи)")


def get_allowed_skips():
    return ALLOWED_SKIPS + 2  # VERY DIFFICULT LOGIC, JUST TRUST ME


def get_check_period() -> float:
    if _is_internet_alive:
        return alive_check_period
    else:
        return dead_check_period


def internet_status_dead():
    global _is_internet_alive
    if not _is_internet_alive:  # already dead - skip
        return

    _is_internet_alive = False
    send_silent_status(STATUS_DEAD)


def internet_status_alive(time_passed):
    global _is_internet_alive
    if _is_internet_alive:  # already alive - skip
        return

    _is_internet_alive = True
    status = STATUS_ALIVE.format(time_passed)
    if time_passed < SILENT_TIME_MINUTES*60:
        send_status(status)
    else:
        send_silent_status(status)


def send_status(status: str, silent=0):  # todo subscribing (upd 21.01.2022: no, thanks :) )
    r = vk.rest.post("messages.send", user_id=user_id, message=status, random=True, silent=silent)
    logging.info(status)
    logging.info(r.json())


def send_silent_status(status: str):
    send_status(status, silent=1)


def no_slash(bytes):
    return str(bytes).replace("\\n", "\n").replace("\\r", "\r")[2:-1]


def run():
    global last_update_time
    updaterThread.start()

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
            lock.release()
        else:
            logging.info(f"received unknown bytes from {address}\n{no_slash(response)}")


sender_period = 60

alive_check_period = sender_period / 2
dead_check_period = sender_period / 4

ALLOWED_SKIPS = 2
SILENT_TIME_MINUTES = 5

STATUS_ALIVE = "Интернет ожил во имя святого Лемжина (спустя {0} секунд)"
STATUS_DEAD = "Инет упал, опять.."

if __name__ == '__main__':
    token = properties.get("token")
    user_id = properties.get("user_id")
    vk = VK(token, user_id)
    _is_internet_alive = True
    last_update_time = time.time()
    lock = Lock()
    updaterThread = Thread(target=t_updater, daemon=True)
    run()
