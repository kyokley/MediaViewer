import logging
from logging.handlers import RotatingFileHandler
from site.settings import loglevel, LOG_FILE_NAME

class LogFile(object):
    logger = None

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogFile, cls).__new__(
                    cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def getLogger(cls):
        if not cls.logger:
            log = logging.getLogger('mediaviewer')
            log.setLevel(loglevel)
            rfh = RotatingFileHandler(LOG_FILE_NAME,
                                      mode='a',
                                      maxBytes=10000000,
                                      backupCount=10,
                                      )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            rfh.setFormatter(formatter)
            log.addHandler(rfh)
            cls.logger = log

        return cls.logger

log = LogFile.getLogger()
