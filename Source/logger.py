import asyncio
import datetime
import time
import shared

backlog = []

def log(text):
    now = datetime.datetime.utcnow().isoformat() + " UTC "
    
    text = str(text)

    text = now + " | " + text

    if len(text) > 1999:
        text = "Too long to log"

    backlog.append(text)