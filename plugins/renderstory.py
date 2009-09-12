# Allow story bodies to conditionally contain substitutions.

import Gyre

def render_story(query, docentity, story, storyenvt):
    return Gyre.template(story.body, storyenvt)
