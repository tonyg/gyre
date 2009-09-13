#!/usr/bin/python
from __future__ import nested_scopes
import sys
import string

from Gyre import *
import Config

def sitemap_main():
    store = config.store
    query = query_for(category = [], mode = 'sitemap', flavour = 'html')

    store.load()

    docenvt = Entity()
    docenvt.flavour = config.store.getFlavour('html')
    docenvt.query = query
    docenvt.config = config
    docenvt.url = config.script_url

    def expand_idx(cat, idx, storyids):
        def process_kids():
            result = []
            for (newcat, (newidx, newstoryids)) in idx.items():
                result.append(expand_idx(cat + [newcat], newidx, newstoryids))
            return string.join(result, '')

        def render_stories():
            stories = [store.getStory(id) for id in storyids]
            stories.sort(key = lambda s: s.mtime, reverse = True)
            result = []
            for story in stories:
                storyenvt = Entity(docenvt)
                storyenvt.story = story
                for prerender_story in config.store.getPlugins('prerender_story'):
                    result.extend(prerender_story(query, docenvt, story, storyenvt))
                result.append(template(docenvt.flavour.sitemap_story, storyenvt))
            return string.join(result, '')

        e = Entity(docenvt)
        e.category = cat
        e.process_kids = process_kids
        e.stories = lambda : map(store.getStory, storyids)
        e.render_stories = render_stories
        return template(docenvt.flavour.sitemap_index, e)

    docenvt.contents = expand_idx([], *config.categoryIndex.root)

    for prerender_document in config.store.getPlugins('prerender_document'):
        prerender_document(query, docenvt)

    store.save()

    sys.stdout.write(template(docenvt.flavour.headers, docenvt))
    sys.stdout.write('\r\n')
    sys.stdout.write(template(docenvt.flavour.document, docenvt))

sitemap_main()
