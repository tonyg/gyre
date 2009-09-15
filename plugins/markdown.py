# An extended markdown syntax.

import Gyre
import markdown2
import os
import re

def escape_md(str):
    return (str
            # To avoid markdown <em> and <strong>:
            .replace('*', markdown2.g_escape_table['*'])
            .replace('_', markdown2.g_escape_table['_']))

class ExtendedMarkdown(markdown2.Markdown):
    wikiish_link = re.compile(r'\[\[([^]|]+)(\|([^]|]+))?\]\]')
    mdash_re = re.compile(r'(\b|\s)--(\b|\s)')
    def __init__(self, link_base):
        self.link_base = escape_md(link_base)
        markdown2.Markdown.__init__(self, extras = ["footnotes", "link-patterns"])

    def _do_link_patterns(self, text):
        replacements = []
        for match in self.wikiish_link.finditer(text):
            replacements.append((match.span(), match.group(1), match.group(3)))
        replacements.reverse()
        for (start, end), href, label in replacements:
            href = escape_md(href)
            if label is None:
                label = os.path.basename(href)
            escaped_href = href.replace('"', '&quot;')  # b/c of attr quote
            text = text[:start] + \
                   ('<a href="%s.html">%s</a>' % \
                    (os.path.join(self.link_base, escaped_href), label)) + \
                   text[end:]
        return self.mdash_re.sub(' &mdash; ', text)

def md_span(text):
    md = ExtendedMarkdown(Gyre.config.renderenvt.url)
    text = md._run_span_gamut(text)
    text = md._unescape_special_chars(text)
    return text

def markdown(text):
    return ExtendedMarkdown(Gyre.config.renderenvt.url).convert(text)

def install(config):
    config.renderenvt.md_span = md_span
    config.renderenvt.markdown = markdown
