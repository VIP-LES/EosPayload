import logging

LOG_FMT = '[%(asctime)s.%(msecs)03d] %(name)s.%(levelname)s: %(message)s'
DATE_FMT = '%Y-%m-%dT%H:%M:%S'


def init_logging(log_filename: str) -> None:
    """ Sets up console and file logging

    :param log_filename: filename to write logs to.  File will be opened in append mode.
    """
    logging.basicConfig(filename=log_filename,
                        filemode='a',
                        format=LOG_FMT,
                        datefmt=DATE_FMT,
                        level=logging.DEBUG,
                        force=True)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(LOG_FMT, DATE_FMT))
    logging.getLogger('').addHandler(console)
