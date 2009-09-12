# Allow story bodies to conditionally contain substitutions. Activate
# this plugin for each story by adding "renderstory" to the list in
# the "Renderers" header.

import Gyre

plugin_order = 200

def prerender_story(query, docentity, story, storyenvt):
    if 'renderstory' in story.renderers:
        story.body_pre_renderstory = story.body
        story.body = Gyre.template(story.body, storyenvt)
    return []
