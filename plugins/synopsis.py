# Provide a routine for producing a "synopsis" of some text (eg. a
# story body).

import Gyre

plugin_order = 50

def make_synopsis(text, maxlen = 500):
    if len(text) > maxlen:
        return text[:maxlen] + '...'
    else:
        return text

def prerender_story(query, docentity, story, storyenvt):
    storyenvt.make_synopsis = make_synopsis
    return []
