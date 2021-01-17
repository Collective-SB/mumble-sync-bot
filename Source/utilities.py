import secrets
import base64
from markdown import Markdown
from io import StringIO
from html.parser import HTMLParser
import re

def generateToken():
    #Base64'd Rickroll.
    easterEgg = "https://bit.ly/3ksSjAl"
    token = secrets.token_urlsafe(64)

    return base64.b64encode(bytes(easterEgg + " " + token, "ascii")).decode("ascii")

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

# THIS DOES NOT SANITISE. DO NOT USE IT WHERE SECURITY IS IMPOTANT.
def stripHTML(html):
    return re.sub('<[^<]+?>', '', html)