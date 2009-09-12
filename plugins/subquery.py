# Provide a routine for rendering subqueries of the story database.

import Gyre

plugin_order = 50

def prerender_story(query, docentity, story, storyenvt):
    def subquery(**kw):
        p = {'flavour': query.flavour}
        p.update(kw)
        q = Gyre.Entity(defaultprops = p)
        subdoc = Gyre.renderQuery(q, docentity.url)
        return subdoc.contents
    storyenvt.subquery = subquery
    return []
