from datetime import datetime


def i(message):
    str_content = message.encode('utf-16', 'surrogatepass').decode('utf-16')
    _GREEN = "\033[32m"
    _RESET = "\033[0m"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{_GREEN}{current_time}: {str_content}{_RESET}")


def d(message):
    str_content = message.encode('utf-16', 'surrogatepass').decode('utf-16')
    _YELLOW = "\033[33m"
    _RESET = "\033[0m"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{_YELLOW}{current_time}: {str_content}{_RESET}")


def e(message):
    str_content = message.encode('utf-16', 'surrogatepass').decode('utf-16')
    _RED = "\033[31m"
    _RESET = "\033[0m"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{_RED}{current_time}: {str_content}{_RESET}")
