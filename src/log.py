from datetime import datetime

LOG_FILE = "data/log.txt"
LOG_LEVELS = ['E', 'W', 'A']

def log(level, text, verbose=False):
    """log program actions to file

    Args:
        level (str): Error level. Levels are E: error, W: warning, A: action
        text (str): Text to log
        verbose (bool): print log to stdout as well
    """
    
    level = level.upper()
    time = datetime.now()
    
    with open(LOG_FILE, 'a+') as fp:
        if level not in LOG_LEVELS:
            fp.write(f'W: {time} log message {text} given wrong level {level}\n')
        else:
            fp.write(f'{level}: {time} {text}\n')
    if verbose:
        if level not in LOG_LEVELS:
            print(f'W: {time} log message {text} given wrong level {level}')
        else:
            print(f'{level}: {time} {text}')