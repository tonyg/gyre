import Gyre
import string
import time

def dateline(story, context):
    # Keep a running dateline.
    mtime = time.localtime(story.mtime)
    this_day = (mtime[0], mtime[1], mtime[2])
    if not context.last_day or context.last_day != this_day:
        context.last_day = this_day
        return Gyre.renderStory(context.flavour, 'dateline', story, context)
    else:
        return ''

def install(config):
    config.renderenvt.dateline = dateline
