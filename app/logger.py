import logging


def setup_logging(log_level=logging.INFO, log_file="app.log", name="app"):
    """Настраивает логгер для приложения."""

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)s: %(name)s - %(message)s',
                'datefmt': '%H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': log_file,
                'level': log_level,
                'formatter': 'standard',
                'mode': 'w',
            },
        },
        'loggers': {
            f"{name}": {  # Имя логгера вашего приложения
                'handlers': ['console', 'file'],  # Здесь добавили 'console'
                'level': log_level,
                'propagate': False,
            },
        },
    })

    return logging.getLogger(name)
