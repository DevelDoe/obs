# auto_stream.py
from obswebsocket import obsws, requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import datetime
import logging
import time

# Setup logging
logging.basicConfig(
    filename="auto_obs.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)


def log_run(name):
    logging.info(
        f"🚀 Job '{name}' triggered at {datetime.datetime.now(tz=eastern)}")


def log_heartbeat():
    logging.info("⏱️ Heartbeat: Scheduler is alive.")


# Setup timezone
eastern = pytz.timezone("US/Eastern")

# OBS websocket config & connect
host = "localhost"
port = 4455
password = ""


def with_obs(func):
    def wrapped():
        # max_retries = 10          # increased retries
        # retry_delay = 60          # wait 10 seconds between tries
        max_retries = 3
        retry_delay = 10
        for attempt in range(1, max_retries + 1):
            try:
                ws = obsws(host, port, password)
                ws.connect()
                logging.info(f"[Attempt {attempt}] Connected to OBS.")
                func(ws)
                ws.disconnect()
                return
            except Exception as e:
                logging.warning(f"[Attempt {attempt}] OBS not ready: {e}")
                time.sleep(retry_delay)
        logging.critical(
            f"Failed to connect to OBS after {max_retries} attempts.")
    return wrapped


@with_obs
def start_stream(ws):
    log_run("start_stream")
    logging.info(f"[{datetime.datetime.now()}] Starting stream")
    ws.call(requests.SetCurrentProgramScene(sceneName="intro"))  # intro scene
    ws.call(requests.StartStream())
    
@with_obs
def switch_to_intro(ws):
    log_run("switch_to_intro")
    logging.info(f"[{datetime.datetime.now()}] Switching to 'intro'")
    ws.call(requests.SetCurrentProgramScene(sceneName="intro"))

@with_obs
def switch_to_live(ws):
    log_run("switch_to_live")
    logging.info(f"[{datetime.datetime.now()}] Switching to 'live'")
    ws.call(requests.SetCurrentProgramScene(sceneName="live"))


@with_obs
def switch_to_end(ws):
    log_run("switch_to_end")
    logging.info(f"[{datetime.datetime.now()}] Switching to 'end'")
    ws.call(requests.SetCurrentProgramScene(sceneName="end"))


@with_obs
def end_stream(ws):
    log_run("end_stream")
    logging.info(f"[{datetime.datetime.now()}] Ending stream")
    ws.call(requests.StopStream())


# Setup scheduler
scheduler = BlockingScheduler(timezone=eastern)

# 🌙 Start stream at 00:00 (Sun–Fri)
scheduler.add_job(
    start_stream,
    CronTrigger(hour=0, minute=0, day_of_week='sun-fri', timezone=eastern)
)

# 🎬 Switch to live scene at 03:55 ET (Mon–Fri)
scheduler.add_job(
    switch_to_live,
    CronTrigger(hour=3, minute=55, day_of_week='mon-fri', timezone=eastern)
)

# 🔚 Switch to end scene at 20:00 ET (Mon–Fri)
scheduler.add_job(
    switch_to_end,
    CronTrigger(hour=20, minute=0, day_of_week='mon-fri', timezone=eastern)
)

# 🛑 Stop stream at 21:00 ET (Mon–Fri)
scheduler.add_job(
    end_stream,
    CronTrigger(hour=21, minute=0, day_of_week='mon-fri', timezone=eastern)
)

# ⏱ Heartbeat every hour
scheduler.add_job(
    log_heartbeat,
    CronTrigger(minute=0, timezone=eastern)
)


logging.info("Scheduler started... (Eastern Time)")
scheduler.start()
