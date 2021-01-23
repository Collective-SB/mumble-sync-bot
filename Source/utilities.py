import secrets
import base64
from markdown import Markdown
from io import StringIO
from html.parser import HTMLParser
import re
import DiscordManager
import Logger

def generateToken():
    #Base64'd Rickroll.
    easterEgg = "https://bit.ly/3ksSjAl"
    token = secrets.token_urlsafe(64)

    return base64.b64encode(bytes(easterEgg + " " + token, "ascii")).decode("ascii")

def generateID(l):
    return secrets.token_urlsafe(l)

#patch the markdown module
def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


# patching Markdown
Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False

def stripMarkdown(mark):
    return __md.convert(mark)

# THIS DOES NOT SANITISE. DO NOT USE IT WHERE SECURITY IS IMPORTANT.
def stripHTML(html):
    return re.sub('<[^<]+?>', '', html)

async def isValidDiscordID(id):
    try:
        Logger.log("Checking if " + str(id) + " is valid.")
        user = await DiscordManager.bot.fetch_user(int(id))
        return True
    except:
        return False

def isPow2(n):
    if (n & (n-1) == 0) and n != 0:
        return True
    else:
        return False