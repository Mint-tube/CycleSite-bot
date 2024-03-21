from colorama import Fore, Back, Style, init
import datetime

__all__ = ['debug', 'info', 'warning', 'error']

init(autoreset=True)

def datestr():
    return f'{Fore.BLACK}{Style.BRIGHT}{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {Style.RESET_ALL}'

def debug(message):
    message = str(message)
    print(datestr() + f'{Style.BRIGHT}{Fore.CYAN}DEBUG    {Style.RESET_ALL}' + message)

def info(message):
    message = str(message)
    print(datestr() + f'{Style.BRIGHT}{Fore.BLUE}INFO     {Style.RESET_ALL}' + message)

def warning(message):
    message = str(message)
    print(datestr() + f'{Style.BRIGHT}{Fore.YELLOW}WARNING  {Style.RESET_ALL}' + message)

def error(message):
    message = str(message)
    print(datestr() + f'{Style.BRIGHT}{Fore.RED}ERROR    {Style.RESET_ALL}' + message)