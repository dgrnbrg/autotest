"""A singleton class for accessing global config values

provides access to global configuration file
"""

__author__ = 'raphtee@google.com (Travis Miller)'

import os
import sys
import ConfigParser
import error


class ConfigError(error.AutotestError):
	pass


class ConfigValueError(ConfigError):
	pass


class global_config(object):

	config = None

	def get_config_value(self, section, key, type=str, default=None):
	        if self.config == None:
	        	self.parse_config_file()
	        	
	        try:
                	val = self.config.get(section, key)
                except:
                        if default == None:
                                msg = ("Value '%s' not found in section '%s'" %
                                      (key, section))
                                raise ConfigError(msg)
                        else:
                                return default

		return self.convert_value(key, section, val, type, default)


	def merge_configs(self, shadow_config):
		# overwrite whats in config with whats in shadow_config
		sections = shadow_config.sections()
		for section in sections:
			# add the section if need be
			if not self.config.has_section(section):
				self.config.add_section(section)
			# now run through all options and set them
			options = shadow_config.options(section)
			for option in options:
				val = shadow_config.get(section, option)
				self.config.set(section, option, val)


	def parse_config_file(self):
		dirname = os.path.dirname(sys.modules[__name__].__file__)
		root = os.path.abspath(os.path.join(dirname, "../../"))
		config_file = os.path.join(root, "global_config.ini")
		self.config = ConfigParser.ConfigParser()
		self.config.read(config_file)

		# now also read the shadow file if there is one
		# this will overwrite anything that is found in the 
		# other config
		config_file = os.path.join(root, "shadow_config.ini")
		if os.path.exists(config_file):
			shadow_config = ConfigParser.ConfigParser()
			shadow_config.read(config_file)
			# now we merge shadow into global
			self.merge_configs(shadow_config)
			
	
	# the values that are pulled from ini
	# are strings.  But we should attempt to
	# convert them to other types if needed.
	def convert_value(self, key, section, value, type, default):
		# strip off leading and trailing white space
		sval = value.strip()
		
		# if length of string is zero then return None
		if len(sval) == 0:
			if type == str:
				return ""
			elif type == bool:
				return False
			elif type == int:
				return 0
			elif type == float:
				return 0.0
			else:
				return None
		
		if type == bool:
			if sval.lower() == "false":
				return False
			else:
				return True
		
		try:
			conv_val = type(sval)
			return conv_val
		except:
			msg = ("Could not covert %s in section %s" % 
				(key, section))
			raise ConfigValueError(msg)
		
		
# insure the class is a singleton.  Now the symbol global_config 
# will point to the one and only one instace of the class
global_config = global_config()
