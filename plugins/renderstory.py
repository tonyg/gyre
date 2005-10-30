# Allow story bodies to conditionally contain substitutions. Activate
# this plugin for each story by setting the "Renderer" header to
# "renderstory".

import Gyre

plugin_order = 200

def prerender_story(query, docentity, story, storyenvt):
    if story.renderer == 'renderstory':
        story.body_pre_renderstory = story.body
        story.body = Gyre.template(story.body, storyenvt)
    return []
