import Gyre
import string
import time

plugin_order = 100

default_config = Gyre.Entity()
default_config.modes = ['snapshot', 'script']

def prerender_story(query, docentity, story, storyenvt):
    # Keep a running dateline.

    my_config = Gyre.config.dateline
    if not my_config:
        my_config = default_config
    if query.mode not in my_config.modes:
        return []

    mtime = time.localtime(story.mtime)
    this_day = (mtime[0], mtime[1], mtime[2])
    if not docentity.last_day or docentity.last_day != this_day:
        docentity.last_day = this_day
        docentity.last_dayfmt = lambda fmt: time.strftime(fmt, mtime)
        docentity.dateline
        return [Gyre.template(docentity.flavour.dateline, storyenvt)]
    else:
        return []
