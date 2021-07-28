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
            if time.time() - lut > 2 * sender_period:
                internet_status_dead()
            else:
                internet_status_alive()
        except Exception as e:
            logging.info(e)
            send_status("dead")


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
    send_status(STATUS_DEAD)


def internet_status_alive():
    global _is_internet_alive
    if _is_internet_alive:  # already alive - skip
        return

    _is_internet_alive = True
    send_status(STATUS_ALIVE)


def send_status(status: str):  # todo subscribing
    r = vk.rest.post("messages.send", user_id=user_id, message=status, random=True)
    logging.info(status)
    logging.info(r.json())


def no_slash(bytes):
    return str(bytes).replace("\\n", "\n").replace("\\r", "\r")[2:-1]


def run():
    global last_update_time
    updater = Thread(target=t_updater, daemon=True)
    updater.start()

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

STATUS_ALIVE = "Интернет ожил во имя святого Лемжина"
STATUS_DEAD = "Инет упал, опять.."

if __name__ == '__main__':
    token = properties.get("token")
    user_id = properties.get("user_id")
    vk = VK(token, user_id)
    _is_internet_alive = True
    last_update_time = time.time()
    lock = Lock()
    run()
