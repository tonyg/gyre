# Standard plugin.
import Gyre
import string
import time
import os

plugin_order = 100

def preprocess(story):
    story.display = Gyre.Entity()
    story.display.category = string.join(story.category, '/')
    return story

def prerender_story(query, docentity, story, storyenvt):
    # Allow mtime to be formatted in the template.
    story.mtimefmt = lambda fmt: time.strftime(fmt, time.localtime(story.mtime))
    return []

def prerender_document(query, docenvt):
    def skip_url(skip):
        if query.mode == 'snapshot':
            if int(skip):
                return os.path.join(*([docenvt.url] + query.category +
                                      ['index-skip' + skip + '.' + query.flavour]))
            else:
                return os.path.join(*([docenvt.url] + query.category + ['index.' + query.flavour]))
        elif query.mode == 'script':
            return os.path.join(*([docenvt.url] + query.category +
                                  ['index.' + query.flavour + '?skip=' + skip]))
        else:
            return ''
            
    if Gyre.config.num_entries:
        next_skip = ''
        prev_skip = ''
        if query.mode in ['snapshot', 'script']:
            basenum = 0
            if query.skip: basenum = int(query.skip)
            prev_skip = basenum - Gyre.config.num_entries
            next_skip = basenum + Gyre.config.num_entries
            if prev_skip < 0: prev_skip = ''
            else: prev_skip = str(prev_skip)
            if next_skip >= docenvt.story_count: next_skip = ''
            else: next_skip = str(next_skip)
        docenvt.skip_url = skip_url
        docenvt.next_skip = next_skip
        docenvt.prev_skip = prev_skip

def filterQueryStories(query, stories):
    if query.skip:
        del stories[:int(query.skip)]
    if Gyre.config.num_entries:
        del stories[Gyre.config.num_entries:]
