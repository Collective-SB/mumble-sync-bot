import InterVars as v
import time
import datetime

class backlog:
    logs = ["Logger Initialised"]

def log(text):
    now = datetime.datetime.utcnow().isoformat() + " UTC "

    text = str(text)

    print(text)
    
    toAppend = now + " | " + text

    if len(toAppend) > 1800:
        warn("Could not log due to message being too large.")
        return

    backlog.logs.append(toAppend)

    if len(backlog.logs) > 10 and "**WARNING: LOGGING BUFFER IS LARGE. DELAYS MAY OCCUR WHEN LOGGING.**" not in backlog.logs:
        backlog.logs.append("**WARNING: LOGGING BUFFER IS LARGE. DELAYS MAY OCCUR WHEN LOGGING.**")

def warn(text):
    now = datetime.datetime.utcnow().isoformat() + " UTC "

    text = str(text)

    print("[WARN]" + text)

    toAppend = "**" + now + " | " + "[WARN] " + text + "**"

    if len(toAppend) > 1800:
        warn("Could not log due to message being too large.")
        return

    backlog.logs.append(toAppend)

    if len(backlog.logs) > 10 and "**WARNING: LOGGING BUFFER IS LARGE. DELAYS MAY OCCUR WHEN LOGGING.**" not in backlog.logs:
        backlog.logs.append("**WARNING: LOGGING BUFFER IS LARGE. DELAYS MAY OCCUR WHEN LOGGING.**")

async def pushLogLoop():
    while True:
        toSend = ""
        for text in backlog.logs:
            if len(toSend) + len(text) < 1800:
                toSend = toSend + "\n" + text
                backlog.logs.remove(text)
            else:
                break

        if toSend != "" and v.botManager.ready == True:
            await v.botManager.bot.get_channel(799300592270442546).send(toSend)

        time.sleep(2)