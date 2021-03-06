__author__ = 'jaat'


import sys
import getopt
import argparse
import subprocess
import os
import re
import json
import configparser


from pprint import pprint
from constants import *
from logger import Logger
from config import Configuration
from keytype import KeyType



keyType = None
flags = {}
args = None

config = Configuration(CONFIG)
logger = Logger(config.getConfig().getboolean(GENERAL, ACTIVATE_COLOR_ON_WINDOWS))



def init():
	global config
	global keyType

	keyType = KeyType[config.get(GENERAL, SOURCE)]

def parseCommandLineArgs():
	parser = argparse.ArgumentParser()
	parser.set_defaults(name='parser')
	subParsers = parser.add_subparsers()
	
	configParser = subParsers.add_parser('config')
	configParser.set_defaults(name='config')
	configParser.add_argument('-f', '--file', help='ADDS THE FILE PATH TO CONFIGURATION')
	configParser.add_argument('-k', '--key-not-found', help='ACTION TO PERFORM WHEN KEY IS NOT FOUND IN USER FILE', choices=['EXIT', 'PASS'], dest='whenKeyNotFound')
	configParser.add_argument('-s', '--source', help='DEFAULT SOURCE FOR KEY, CURRENTLY SET TO BOOKMARK', choices=['DATA', 'BOOKMARK'])
	configParser.add_argument('-c', '--color-on-windows', help='ACTIVATES COLORS ON WINDOWS CMD', choices=['TRUE', 'FALSE'], dest='activeColorOnWindows')
	
			
	execParser = subParsers.add_parser('exec')
	execParser.set_defaults(name='exec')
	execParser.add_argument('command', help='COMMAND TO EXECUTE')
	execParser.add_argument('key', help='KEY WHOSE DATA WILL BE PASSED AS ARGUMENT TO COMMAND')
	execParser.add_argument('-f', '--file',  help='USER FILE FROM WHICH KEY WILL BE PARSED')
	execParser.add_argument('-a', '--append-arg', help='INSTEAD OF PASSING AS ARGUMENT TO COMMAND ARGUMENT IS CONCATENATED WITH COMMAND STRING', action='store_true', dest='appendArg')
	execParser.add_argument('-k', '--key-not-found', help='ACTION TO PERFORM WHEN KEY IS NOT FOUND, EXIT OR PASS KEY STRING ITSELF TO THE COMMAND', choices=['EXIT', 'PASS'], dest='whenKeyNotFound')
	execParser.add_argument('-s', '--shell', help='INSTEAD OF EXECUTING COMMAND, PASSES COMMAND TO SHELL', action='store_true')
	# execParser.add_argument('-i', '--ignore-colon', help='IGNORES BEHAVIOR OF COLON WHEN SOURCE IS "BOOKMARK"', action='store_true', dest='ignoreColon')
			
	sourceGroup = execParser.add_mutually_exclusive_group()
	sourceGroup.add_argument('-d', '--data', help='SETS THE KEY SOURCE AS DATA', action='store_true')
	sourceGroup.add_argument('-b', '--bookmark', help='SETS THE KEY SOURCE AS BOOKMARKS', action='store_true')
	
	
	infoParser = subParsers.add_parser('info')
	infoParser.set_defaults(name='info')
	infoParser.add_argument('-s', '--source', help='DEFAULT SOURCE FOR KEY', action='store_true')
	infoParser.add_argument('-k', '--key-not-found', help='DEFAULT ACTION WHEN KEY IS NOT FOUND (EXIT, PASS)', action='store_true', dest='whenKeyNotFound')
	infoParser.add_argument('-f', '--file', help='PATH FOR DEFAULT USER FILE', action='store_true')
	infoParser.add_argument('-c', '--color-on-windows', help='WHETHER COLORS ARE ACTIVE ON WINDOWS CMD', action='store_true', dest='activeColorOnWindows')
	
	return parser.parse_args()
	
def execHandler(args):
	global keyType
	global config
	global flags
	global logger

	flags['d'] = args.data
	flags['a'] = args.appendArg
	flags['b'] = args.bookmark

	if args.data:
		keyType = KeyType.DATA
	elif args.bookmark:
		keyType = KeyType.BOOKMARK

	file = ''		
		
	if not args.file:
		file = config.get(USER, FILE)
		if not file or file == '':
			logger.error('-f IS REQUIRED')
			logger.note('USE -u <FILE_PATH> TO ADD FILE TO CONFIGURATION AND TO USE WITHOUT -f OPTION')
			exit(-1)
	else: file = args.file		
	
	return (file, args.command, args.key)
		
def configHandler(args):
	with open(CONFIG, 'a+') as configFile:
		if args.source:
			config.set(GENERAL, SOURCE, args.source)
			
		if args.file:
			config.set(USER, FILE, args.file)

		if args.whenKeyNotFound:
			config.set(GENERAL, WHEN_KEY_NOT_FOUND, args.whenKeyNotFound)

		if args.activeColorOnWindows == 'TRUE':
			config.set(GENERAL, ACTIVATE_COLOR_ON_WINDOWS, 'TRUE')
		else:
			config.set(GENERAL, ACTIVATE_COLOR_ON_WINDOWS, 'FALSE')

	exit(2)

def infoHandler(args):
	global config
	global logger

	if args.source is True:
		logger.log('DEFAULT SOURCE: ' + config.get(GENERAL, SOURCE))

	if args.file is True:
		logger.log('USER FILE PATH: ' + config.get(USER, FILE))

	if args.whenKeyNotFound is True:
		logger.log('DEFAULT ACTION WHEN KEY IS NOT FOUND: ' + config.get(GENERAL, WHEN_KEY_NOT_FOUND))

	if args.activeColorOnWindows is True:
		logger.log('IF COLOR IS ACTIVE ON WINDOWS: ' + config.get(GENERAL, ACTIVATE_COLOR_ON_WINDOWS))

	if args.whenKeyNotFound is False and args.source is False and args.file is False and args.activeColorOnWindows is False:
		
		logger.log('DEFAULT SOURCE: ' + config.get(GENERAL, SOURCE))
		logger.log('USER FILE PATH: ' + config.get(USER, FILE))
		logger.log('DEFAULT ACTION WHEN KEY IS NOT FOUND: ' + config.get(GENERAL, WHEN_KEY_NOT_FOUND))
		logger.log('IF COLOR IS ACTIVE ON WINDOWS: ' + config.get(GENERAL, ACTIVATE_COLOR_ON_WINDOWS))


	exit(2)

def getFileContent(fileName):
	global logger
	try:
		file = open(fileName, 'r')
		json = file.read()
		file.close()

		return json
	except Exception:
		logger.error('ERROR WHILE OPENING OR READING FILE')		
		exit(-1)

	return None

def parseFileContent(inputFile):
	global logger
	content = getFileContent(inputFile)
	try:
		parsedJSON = json.loads(content)
	except Exception:
		logger.error('INVALID JSON FORMAT')
		exit(-1)

	return (parsedJSON['COMMANDS'], parsedJSON['BOOKMARKS'], parsedJSON['DATA'])

def getCommand(commands, command):
	global args

	def parseCommandOptions(command):
		options = dict()
		if 'a' in command:
			options['a'] = command['a']
		else: options['a'] = False

		if 's' in command:
			options['s'] = command['s']
		else: options['s'] = False

		return options

	if command in commands:
		commandOptions = parseCommandOptions(commands[command])			
		return commands[command]['cmd'], commandOptions
	else: 
		commandOptions = {
			'a': args.appendArg,
			'k': args.whenKeyNotFound,
			's': args.shell,
		}
		return (command, commandOptions)

def getKeyValue(content, key, type=KeyType.BOOKMARK):
	global logger
	global args

	onKeyNotFound = config.get(GENERAL, WHEN_KEY_NOT_FOUND)

	def resolveKey(content, key):
		keys = key.split(':')
		parent = keys[0]
		key = ''.join(keys[1:])

		parentValue = content['BOOKMARK'][parent]
		resolvedKey = parentValue + '.' + key

		return getDataValue(content['DATA'], resolvedKey)
	
	def getDataValue(content, key):
		value = content
		tempk = ''
		try:
			for k in key.split('.'):
				tempk = k
				value = value[k]

			if isinstance(value, dict):
				logger.info('NOT A COMPLETE KEY')
				pprint(value)
			elif isinstance(value, str):
				return value, False

		except Exception:
			logger.error('KEY "' + tempk + '" NOT FOUND')
			if onKeyNotFound == 'PASS':
				logger.info('PASSING PROVIDED KEY DIRECTLY TO COMMAND')				
			elif onKeyNotFound == 'EXIT': exit(-1)
		return (key, True)

	def getBookmarkValue(content, key):
		value = None
		try:
			key = content['BOOKMARK'][key]
			return getDataValue(content['DATA'], key)
		except Exception:
			logger.error('KEY "' + key + '" NOT FOUND')
			if onKeyNotFound == 'PASS':
				logger.info('PASSING PROVIDED KEY DIRECTLY TO COMMAND')				
			elif onKeyNotFound == 'EXIT': exit(-1)
		return (key, True)


	if type == KeyType.DATA:
		return getDataValue(content['DATA'], key)
	elif type == KeyType.BOOKMARK:
		if key.count(':') >= 1:
			if key.count(':') > 1:
				logger.warn('MULTIPLE ":" FOUND IN BOOKMARK KEY')
				logger.info('FIRST ":" WILL BE USED AS REFERENCE TO PARSE KEY')
				
			return resolveKey(content, key)
		else:
			return getBookmarkValue(content, key)

def executeCommand(command, commandOptions, value, KEY_FOUND):
	global logger

	if flags['a'] is True or commandOptions['a'] is True:
		try:
			subprocess.run(command + value, shell=(commandOptions['s'] or args.shell))
		except Exception:
			logger.error('ERROR IN COMMAND "' + command+value + '"')
			exit(-1)
	else:
		try:
			subprocess.run([command, value], shell=(commandOptions['s'] or args.shell))
		except Exception:
			logger.error('ERROR IN COMMAND "' + command + ' ' + value + '"')
			exit(-1)







def main():
	global args
	init()	
	args = parseCommandLineArgs()

	if args.name == 'config': configHandler(args)
	elif args.name == 'info': infoHandler(args)
	
	elif args.name == 'exec': 
		(file, command, key) = execHandler(args)

		(commands, bookmarks, data) = parseFileContent(file)

		(command, commandOptions) = getCommand(commands, command)
		(value, KEY_NOT_FOUND) = getKeyValue({ 'DATA':data,'BOOKMARK':bookmarks }, key, type=keyType)

		executeCommand(command, commandOptions, value, not KEY_NOT_FOUND)
	else: exit(-1)
	

	




if __name__ == '__main__':
	main()
