import time
from colorama import Fore, Style

class Logger:
    @staticmethod
    def info(content):
        message = f"{Fore.LIGHTBLACK_EX}[{time.strftime('%H:%M:%S', time.localtime())}] {Fore.GREEN}{Style.BRIGHT}<+>{Style.RESET_ALL} {Fore.RESET}{content}{Fore.RESET}"
        print(message)

    @staticmethod
    def error(content):
        message = f"{Fore.LIGHTBLACK_EX}[{time.strftime('%H:%M:%S', time.localtime())}] {Fore.RED}{Style.BRIGHT}<->{Style.RESET_ALL} {Fore.RESET}{content}{Fore.RESET}"
        print(message)