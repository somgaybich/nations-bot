import logging

def log_setup():
    # Clears preexisting log data
    with open("logs/last.log", 'w') as f:
        pass

    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", datefmt='%H:%M:%S')

    file_handler = logging.FileHandler('logs/last.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)
    # console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    # root.addHandler(console_handler)