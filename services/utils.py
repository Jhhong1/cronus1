import os
import time
import uuid
import logging


logger = logging.getLogger()


def remove_file(file_path):
    logger.info("file path: {}".format(file_path))
    if os.path.exists(file_path):
        os.remove(file_path)


def generate_uuid():
    return str(uuid.uuid5(uuid.NAMESPACE_OID, str(time.time()))).replace('-', '')
