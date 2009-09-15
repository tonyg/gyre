import Gyre
import re
import time

timestampre = re.compile('[<"](\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d) \S+[">]')

def preprocess(story):
    m = timestampre.match(getattr(story, 'time-stamp') or '')
    if m:
        x = map(lambda i: int(m.group(i)), range(1, 7))
        x.extend([-1, 0, -1])
        story.mtime = int(time.mktime(x))
    return story

def install(config):
    config.store.addPreprocessor(preprocess)
