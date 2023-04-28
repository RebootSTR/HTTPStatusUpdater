# @rebootstr
from client import telegram_main
from server.StatusChecker import StatusChecker

if __name__ == "__main__":
    # start server checker
    StatusChecker().run(telegram_main.send_status, telegram_main.onAliveReceived)
    # start telegram bot
    telegram_main.main()
