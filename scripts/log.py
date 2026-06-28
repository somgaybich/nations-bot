import logging
from pathlib import Path

def log_setup(destination: str = "logs/last.log", console: bool = False):
    """
    Configures logging for a script.
    
    :param destination: The file to write the logs to.
    :param console: Whether to write logs to the console.
    :type destination: str
    :type console: bool
    """
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text("")

    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", datefmt='%H:%M:%S')

    file_handler = logging.FileHandler(destination, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    if console:
        root.addHandler(console_handler)