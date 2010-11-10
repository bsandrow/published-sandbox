#!/usr/bin/env python

import lxml.etree, lxml.html

class HNCommon(object):
    @classmethod
    def from_url(class,url):
        return class(lxml.html.parse(url))

    @classmethod
    def from_string(class,string):
        return class(lxml.html.fromstring(string))

    def __init__(self,doc):
        self.parse(doc)

class HNComment(object):
    text            = None
    user            = None
    comment_no      = None
    permalink       = None
    parent_comment  = None
    level           = None
    children        = []

class HNCommentTree(HNCommon):
    # Path that should specify all of the comment table (one comment per table). Thus far this has
    # only been tested on story urls. This will probably break on pages that *only* contain comment
    # trees or singular comments. A function to determine which type of page we are on and use a
    # particular XPath in each case should probably be created at some point to make this class
    # functional.
    xpath       = '//table[1]/tr[3]/td/table[2]//table'
    comments    = None

    def parse(self,doc):
        comments        = doc.xpath(self.xpath)
        self.comments   = {}
        prev_comment    = None
        for comment in comments:
            c               = HNComment()
            c.user          = comment.xpath('.//td[3]/div/span/a')[0].text_content()
            c.comment_no    = comment.xpath('.//td[3]/div/span/a')[1].get('href').replace('item?id=','')
            c.text          = lxml.html.tostring(comment.xpath('.//td[3]/span')[0])

            # Convert the spacing to an indent-level (0 being the top-level). Spacing is in
            # increments of 40 pixels
            c.level = int(comment.xpath('.//td[1]/img')[0].get('width')) / 40

            # If this is a top-level comment, just cleanup and skip to the next iteration.
            if c.comment_level == 0:
                prev_comment                = c
                self.comments[c.comment_no] = c
                continue

            # If we've increased the level since the last comment, it means that we're a child
            # comment. Record this, clean up, and go to the next iteration.
            if c.level > prev_comment.level:
                prev_comment.children.append(c.comment_no)
                c.parent_comment_no         = prev_comment.comment_no
                self.comments[c.comment_no] = c
                prev_comment                = c
                continue

            # Traverse back up the tree to find the parent comment
            while (c.level <= prev_comment.level):
                prev_comment = self.comment[prev_comment.parent_comment_no]
            c.parent_comment_no         = prev_comment.comment_no
            self.comments[c.comment_no] = c
            prev_comment                = c

        self._populate_children()

    def _populate_children(self):
        for comment_no in self.comments.keys():
            self.comments[comment_no].children = [
                cno for cno in self.comments.keys()
                    if self.comments[cno].parent_comment_no = comment_no
            ]

class HNStory(HNCommon):
    # XPath to the table with the story info. This XPath should always work, so long as the page is
    # a HN story page.
    xpath   = '//table[1]/tr[3]/td/table[1]'
    text    = None
    user    = None
    title   = None
    story   = None
    points  = None
    comments= None

    def __init__(self,doc):
        self.parse_story(doc)
        self.parse_comments(doc)

    def parse_story(self,doc):
        candidates = doc.xpath(self.xpath)
        if len(candidates) > 1:
            raise HNScrapeError("Error: Found multiple tables which might include the story.")
        if len(candidates) < 1:
            raise HNScrapeError("Error: Not a story page")
        story_table = candidates[0]

        title_element   = story_table.cssselect('td.title')[0]
        subtext_element = story_table.cssselect('td.subtext')[0]

        self.title     = title_element.text_content().strip()
        self.story     = title_element.xpath('a[1]')[0].get('href')
        self.user      = subtext_element.xpath('a[1]')[0].text_content()
        self.points    = subtext_element.xpath('span[1]')[0].text_content().strip().replace(' points','')

    def parse_comments(self,doc):
        pass
