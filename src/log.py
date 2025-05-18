import os
import logging
import pathlib

def config_log():
    pathlib.Path("log").mkdir(exist_ok = True)

    log_fmt = logging.Formatter(
        fmt = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S.%(msecs)03d"
    )

    file_h = logging.FileHandler(os.path.join("log", "log.txt"), mode = "a", encoding="utf-8",)
    file_h.setFormatter(log_fmt)
    console_h = logging.StreamHandler()
    console_h.setFormatter(log_fmt)

    logging.basicConfig(
        level       = logging.INFO,
        handlers    = [ file_h, console_h ]
    )
