import time


def spin() -> None:
    """ Loops forever. """
    while True:
        time.sleep(10)


def validate_process_name(name: str) -> bool:
    """ enforces alphanumeric+hyphens for process/thread names for consistency & compatability
    :param name: the name to validate
    :return true if valid, false otherwise
    """
    return name.isascii() and name.replace("-", "").isalnum() and name.lower() == name
