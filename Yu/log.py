import logging

logger = logging.getLogger(__name__)
lgfmt = logging.Formatter("%(asctime)s | %(filename)s #%(funcName)s | %(levelname)s | %(message)s")
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(lgfmt)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

def logDebug(msg):
    logger.debug(msg)

def logInfo(msg):
    logger.info(msg)

def logWarn(msg):
    logger.warning(msg)

def logErr(msg):
    logger.error(msg)

def logCritical(msg):
    logger.critical(msg)
