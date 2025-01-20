import logging
import betterlogging as bl
import json
from datetime import date, datetime

FILE_LOG_LEVEL = 25
LOG_LEVEL_NAME = "FileLog"
logging.addLevelName(FILE_LOG_LEVEL, LOG_LEVEL_NAME)

def setup_file_logger(path: str = "tgbot/logs/", log_name: str = date.isoformat(datetime.now())):
    def file_logger(self, message, extra_data = {}, *args, **kwargs):
        if self.isEnabledFor(FILE_LOG_LEVEL):
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"]["extra_data"] = json.dumps(extra_data)
            self._log(FILE_LOG_LEVEL, message, args, **kwargs)

    logging.Logger.filelog = file_logger

    logger = logging.getLogger('filelog')
    logger.setLevel(FILE_LOG_LEVEL)

    file_handler = logging.FileHandler(f"{path}{log_name}.log")
    file_handler.setLevel(FILE_LOG_LEVEL)

    formatter = bl.Formatter(
        fmt="[%(asctime)s] %(filename)s:%(lineno)d #%(levelname)-8s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

file_logger = setup_file_logger(path = "logs/").filelog