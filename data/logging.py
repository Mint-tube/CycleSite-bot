from colorama import Fore, Back, Style, init
import datetime

init(autoreset=True)

def datestr():
    return f'{Fore.BLACK}{Style.DIM}{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {Style.RESET_ALL}'

def debug(message):
    print(datestr() + f'{Style.BRIGHT}{Fore.CYAN}DEBUG    {Style.RESET_ALL}' + message)

def info(message):
    print(datestr() + f'{Style.BRIGHT}{Fore.BLUE}INFO     {Style.RESET_ALL}' + message)

def warning(message):
    print(datestr() + f'{Style.BRIGHT}{Fore.YELLOW}WARNING  {Style.RESET_ALL}' + message)

def error(message):
    print(datestr() + f'{Style.BRIGHT}{Fore.RED}ERROR    {Style.RESET_ALL}' + message)