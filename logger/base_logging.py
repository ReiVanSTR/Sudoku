import logging
import betterlogging as bl


def setup_logging(loggig_level):
    log_level = loggig_level
    bl.basic_colorized_config(level=log_level)
    
    logging.basicConfig(
        level=loggig_level,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configurated")