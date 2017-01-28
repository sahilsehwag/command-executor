from colorama import Fore, Back, init, Style

class Logger():
	def __init__(self, windows=False):
		if windows:
			init(autoreset=True)		

	def log(self, msg):
		print(Fore.WHITE + msg + Style.RESET_ALL)

	def error(self, msg):
		print(Fore.RED + 'ERROR: ' + msg + Style.RESET_ALL)		

	def warn(self, msg):
		print(Fore.YELLOW + 'WARNING: ' + msg + Style.RESET_ALL)

	def info(self, msg):
		print(Fore.GREEN + 'INFO: ' + msg + Style.RESET_ALL)

	def note(self, msg):
		print(Fore.CYAN + 'NOTE: ' + msg + Style.RESET_ALL)