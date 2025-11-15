import logging
from logging.handlers import StreamHandler

from django.conf import settings


class LogFile(object):
    logger = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogFile, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def getLogger(cls):
        if not cls.logger:
            log = logging.getLogger("mediaviewer")
            log.setLevel(settings.LOG_LEVEL)
            # fh = RotatingFileHandler(
            #     settings.LOG_FILE_NAME,
            #     mode="a",
            #     maxBytes=10000000,
            #     backupCount=10,
            # )
            fh = StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh.setFormatter(formatter)
            log.addHandler(fh)
            cls.logger = log

        return cls.logger


log = LogFile.getLogger()
