# List paging.
import Gyre
import string
import time
import os

def skip_url(url, context, skip):
    category = context.category or []
    flavour = context.flavour

    if context.mode == 'snapshot':
        i = ('index-skip' + str(skip)) if skip else 'index'
        return os.path.join(*([url] + category + [i + '.' + flavour]))
    elif context.mode == 'script':
        skip_extension = ('?skip=%s&num_entries=%s' % (skip, (context.num_entries or 1))) if skip else ''
        return os.path.join(*([url] + category + ['index.' + flavour + skip_extension]))
    else:
        return ''

def pagedRender(flavour, variant, stories, context):
    stories = list(stories)
    stories.sort(key = lambda s: Gyre.config.store.getStory(s).mtime, reverse = True)

    total_count = len(stories)

    skip = context.skip or 0
    num_entries = context.num_entries or 1
    prev_skip = skip - num_entries
    next_skip = skip + num_entries

    if prev_skip <= 0:
        prev_skip = 0
    if next_skip >= total_count:
        next_skip = 0

    if skip:
        del stories[:skip]
    if num_entries:
        del stories[num_entries:]

    context.next_skip = next_skip
    context.prev_skip = prev_skip
    return Gyre.renderStories(flavour, variant, set(stories), context)

def install(config):
    config.renderenvt.pagedRender = pagedRender
    config.renderenvt.skip_url = skip_url
