import logging

"""
Future work:
    Duplicates logger class functionality to add decorators at a later date.
"""

class CreateLogger():
    def __init__(self, name):
        """
        Initialises a logger object with the specified name, handler, formatter, and parameters.

        Args: 
            name (str) - The name of the logger to create
        """
        self.logger = logging.getLogger(name)
        self.handler = logging.FileHandler('{}.log'.format(name), mode='a')
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.set_parameters()

    def set_parameters(self):
        """
        Configures the logger object by setting its level, formatter, and handler.
        """
        self.logger.setLevel(logging.INFO)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)