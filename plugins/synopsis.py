# Provide a routine for producing a "synopsis" of some text (eg. a
# story body).

import Gyre

def make_synopsis(text, maxlen = 500):
    if len(text) > maxlen:
        return text[:maxlen] + '...'
    else:
        return text

def install(config):
    config.renderenvt.make_synopsis = make_synopsis
