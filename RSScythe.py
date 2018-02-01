#!/usr/bin/python2.7

from jinja2 import Template
from urllib2 import urlopen
from os import path, stat, mkdir
from dateutil import parser

import feedparser
import pickle
import datetime

import dill
# Character code fix
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class RSS(object):
    def __init__(self, name, url=None, downloadHTML=True,
                 parseContent=lambda x: x, directory=""):
        if url is not None:
            self.url = url
            self.name = name
            self.savedData = []
            self.etag = None
            self.modified = "0"
            self.downloadHTML = downloadHTML
            self.parseContent = parseContent
            self.directory = directory

            self.saveRSS()
        else:
            if path.isfile(self.directory + name + ".pickle"):
                self = pickle.load(
                    open(self.directory + name + ".pickle", "rb"))
                self.downloadHTML = downloadHTML
            else:
                raise Exception("There is no RSS feed of name " +
                                name + " in this directory.")

    def export2HTML(self):
        with open('generic_template.html', "r") as f:
            template = Template(f.read())
            return template.render(
                menu_list=self.savedData
                title = "RSScythe"
            )

    def saveRSS(self):
        with open(self.directory + self.name + ".pickle", "wb") as f:
            pickle.dump(self, f)

    def updateFeed(self):
        data = feedparser.parse(
            self.url, etag=self.etag, modified=self.modified)
        if data.status == 304:  # Feed not modified
            return {"items": []}
        else:
            try:
                self.etag = data.etag
            except:
                None
            try:
                self.modified = data.modified
            except:
                None
            return data

    def downloadHTMLPage(self, url, name):
        response = urlopen(url)
        with open(self.directory + self.name + "/" + name + ".html", "w") as f:
            f.write(self.parseContent(response.read()))

    def parseFeed(self, data, overwrite):
        if self.downloadHTML:
            try:  # create space for materials
                stat(self.name)
            except:
                mkdir(self.name)

        parsedData = []

        for item in data["items"]:
            if item["published"] <= self.modified and self.modified != "0":
                continue
            title = item["title"]
            link = item["link"]
            content = self.parseContent(item["summary"])
            if (self.downloadHTML
                and (not path.isfile(self.name + "/" + title)
                     or overwrite)):
                self.downloadHTMLPage(link, title)
                item = {"name": title, "location": self.name +
                        "/" + title + ".html", "src": ""}
            else:
                item = {"name": title, "location": self.name +
                        "/" + title + ".html", "src": content}
            parsedData.append(item)
        return parsedData

    def runFeed(self, overwrite=False):
        data = self.updateFeed()
        parsedData = self.parseFeed(data, overwrite)
        self.savedData += parsedData
        self.export2HTML()
        self.saveRSS()


class RSSBouncer(RSS):
    def __init__(self, name, url=None, downloadHTML=True, subtitle="",
                 selfURL="", parseContent=lambda x: x):
        self.selfURL = selfURL
        self.subtitle = subtitle
        self.ID = selfURL
        super(RSSBouncer, self).__init__(name,
                                         url=url,
                                         downloadHTML=downloadHTML,
                                         parseContent=parseContent)

    # Download HTML, return as string.
    def downloadHTMLPage(self, url):
        response = urlopen(url)
        return self.parseContent(response.read())

    # Redirect inherited function to export2XML
    def export2HTML(self):
        self.export2XML()

    # Export contained data as xml (RSS feed)
    def export2XML(self):
        with open(self.name + ".rss", "w") as fs:
            with open('atom_template.xml', "r") as f:
                template = Template(f.read())
                fs.write(template.render(
                    items=self.savedData,
                    title=self.name,
                    subtitle=self.subtitle,
                    ID=self.ID,
                    time=datetime.datetime.utcnow().isoformat('T') + "Z",
                    selfURL=self.selfURL
                ))

    # Parse selected feed (summary, published) and add news to parsedData.
    def parseFeed(self, data, overwrite):
        parsedData = []
        for item in data["items"]:
            if item["published"] <= self.modified and self.modified != "0":
                continue
            if self.downloadHTML:
                item["summary"] = self.downloadHTMLPage(item["link"])
            else:
                item["summary"] = self.parseContent(item["summary"])
            item["published"] = (parser.parse(
                item["published"])).isoformat('T')
            parsedData.append(item)
        return parsedData
