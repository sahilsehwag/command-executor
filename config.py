import configparser
from logger import Logger
from constants import *
from keytype import KeyType

class Configuration:
	def __init__(self, file):
		self.logger = Logger()
		try:
			self.file = file
			self.config = configparser.ConfigParser()

			try:
				open(self.file, 'r')
			except:
				self.init()

			self.config.read(self.file)
		except:
			self.logger.error('CANNOT CREATE OR WRITE TO CONFIG FILE')
			self.logger.note('MAKE SURE SCRIPT HAS READ AND WRITE PERMISSIONS')
			self.logger.note('DON\'T MANAUALLY EDIT config.ini FILE')
			exit(-1)

	
	def init(self):		
		self.set(GENERAL, SOURCE, KeyType.DATA.name)
		self.set(GENERAL, WHEN_KEY_NOT_FOUND, 'EXIT')
		self.set(GENERAL, ACTIVATE_COLOR_ON_WINDOWS, 'TRUE')
		self.set(USER, FILE, '')

	
	def get(self, section, key):
		try:
			return self.config.get(section, key)
		except:
			self.logger.error('SOME ERROR OCCURED WHILE TRYING TO READ FROM CONFIG FILE')
			self.logger.note('MAKE SURE SCRIPT HAS READ AND WRITE PERMISSIONS')
			self.logger.note('DON\'T MANAUALLY EDIT config.ini FILE')			
			exit(-1)

	
	def set(self, section, key, value):
		try:
			with open(self.file, 'w+') as configFile:
				if not self.config.has_section(section):
					self.config.add_section(section)
				self.config[section][key] = value
				self.config.write(configFile)
		except:
			self.logger.error('SOME ERROR OCCURED WHILE TRYING TO WRITE CONFIG FILE')
			self.logger.note('MAKE SURE SCRIPT HAS READ AND WRITE PERMISSIONS')
			self.logger.note('DON\'T MANAUALLY EDIT config.ini FILE')
			exit(-1)
			
	
	def getConfig(self):
		return self.config