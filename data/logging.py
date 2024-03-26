from colorama import Fore, Back, Style, init
import datetime

__all__ = ['debug', 'info', 'warning', 'error']

init(autoreset=True)

def datestr():
    return f'{Fore.BLACK}{Style.BRIGHT}{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {Style.RESET_ALL}'

def debug(*content):
    message = [str(x) for x in content]
    print(datestr() + f'{Style.BRIGHT}{Fore.CYAN}DEBUG    {Style.RESET_ALL}' + ' '.join(message))

def info(*content):
    message = [str(x) for x in content]
    print(datestr() + f'{Style.BRIGHT}{Fore.BLUE}INFO     {Style.RESET_ALL}' + ' '.join(message))

def warning(*content):
    message = [str(x) for x in content]
    print(datestr() + f'{Style.BRIGHT}{Fore.YELLOW}WARNING  {Style.RESET_ALL}' + ' '.join(message))

def error(*content):
    message = [str(x) for x in content]
    print(datestr() + f'{Fore.RED}ERROR    {Style.RESET_ALL}' + ' '.join(message))