import logging
import time
from threading import Thread, Lock
from client.dictionary import *

from server.HTTPServer import HTTPServer

file_log = logging.FileHandler("../log.log")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("").addHandler(file_log)

SENDER_PERIOD = 60  # время между отправками запросов от микроконтроллера
ALIVE_CHECK_PERIOD = SENDER_PERIOD / 2  # время проверки получения запросов, когда интернет доступен (реже)
DEAD_CHECK_PERIOD = SENDER_PERIOD / 4  # время проверки получения запросов, когда интернет не доступен (чаще)

ALLOWED_SKIPS = 2  # количество разрешенных пропусков сигналов (защита от кратковременных сбоев)
SILENT_TIME_MINUTES = 5  # время в течении которого сообщения от бота отправляются без звука


def get_allowed_skips():
    return ALLOWED_SKIPS + 2  # VERY DIFFICULT LOGIC, JUST TRUST ME


# метод удаления слешей из строки
def no_slash(bytes):
    return str(bytes).replace("\\n", "\n").replace("\\r", "\r")[2:-1]


class StatusChecker:

    def __init__(self):
        self._is_internet_alive = True
        self.last_update_time = time.time()
        self.deadTime = 0
        self.lock = Lock()

    def t_updater(self, sendStatusFunc):
        while True:
            try:
                check_period = self.get_check_period()
                time.sleep(check_period)
                self.lock.acquire()
                lut = self.last_update_time
                self.lock.release()
                time_passed = time.time() - lut
                if time_passed > get_allowed_skips() * SENDER_PERIOD:
                    self.internet_status_dead(lut, sendStatusFunc)
                else:
                    self.internet_status_alive(sendStatusFunc)
            except Exception as e:
                logging.info(e)
                sendStatusFunc(CHECKER_ERROR)

    def get_check_period(self) -> float:
        if self._is_internet_alive:
            return ALIVE_CHECK_PERIOD
        else:
            return DEAD_CHECK_PERIOD

    def internet_status_dead(self, lastUpdateTime, sendStatusFunc):
        if not self._is_internet_alive:  # already dead - skip
            return

        self._is_internet_alive = False
        sendStatusFunc(STATUS_DEAD, silent=1)
        self.deadTime = lastUpdateTime

    def internet_status_alive(self, sendStatusFunc):
        if self._is_internet_alive:  # already alive - skip
            return

        _is_internet_alive = True
        timePassed = time.time() - self.deadTime
        status = STATUS_ALIVE.format(int(timePassed))
        if timePassed > SILENT_TIME_MINUTES * 60:
            sendStatusFunc(status)
        else:
            sendStatusFunc(status, silent=1)

    def t_listener(self):
        server = HTTPServer()

        while True:
            try:
                response, address = server.get_bytes()
            except Exception as e:
                logging.info(f"something wrong with connection: {e}")
                continue
            if response == b"INTERNET IS ALIVE":
                self.lock.acquire()
                self.last_update_time = time.time()
                logging.info("alive received from " + str(address))
                self.lock.release()
            else:
                logging.info(f"received unknown bytes from {address}\n{no_slash(response)}")

    def run(self, sendStatusFunc):
        updaterThread = Thread(target=self.t_updater, args=(sendStatusFunc,), daemon=True)
        updaterThread.start()
        listenerThread = Thread(target=self.t_listener, daemon=True)
        listenerThread.start()
