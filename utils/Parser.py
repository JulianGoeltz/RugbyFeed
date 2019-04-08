#!/usr/bin/env python3
from bs4 import BeautifulSoup
import json
import urllib.request as urllib2
from pprint import pprint, pformat as pf


def clearOfRandNandT(text):
    return text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')


with open('./utils/config_sensitive.json', 'r') as f:
    config_sensitive = json.load(f)


class PARSER:
    def __init__(self):
        self.update()
        # self.currentMatches = False
        # self.currentMessages = False
        pass

    def update(self):
        html_page = urllib2.urlopen(config_sensitive['ticker_url'])
        html_page_read = str((html_page.read()).decode('utf-8'))
        self.soup = BeautifulSoup(
            html_page_read,
            'html.parser')
        self.currentMatches = False
        self.currentMessages = False
        # print(self.soup.pretify())

    def returnNumberOfMessages(self):
        if self.currentMessages:
            return self.numberOfMessages

        self.numberOfMessages = len(self.returnMessages())
        return self.numberOfMessages

    def returnMatches(self):
        if self.currentMatches:
            return self.matches

        all_matches = {}
        duplicates = {}
        for item_match in self.soup.find_all('table', attrs=('class', 'ticker')):
            colour = item_match['style'][18:-1]
            colour = colour if len(colour) <= 7 else colour[0:7]
            name = item_match.find('strong').get_text()
            points = item_match.find('td', attrs=('class', 'points')).parent.get_text()
            points = points.strip().replace('\n', '')
            matchStatus = item_match.find(
                'span', attrs=('class', 'small')).get_text()
            matchStatus = matchStatus[1:-1].strip()
            if colour in all_matches:
                if colour not in duplicates:
                    duplicates[colour] = [all_matches[colour]]
                duplicates[colour].append((name, points, matchStatus))
                continue
            all_matches[colour] = (name, points, matchStatus)
            # return  # exit()
        if len(duplicates) != 0:
            print("Error because of duplicate matches (according to their colour):")
            pprint(duplicates)

        # print("Available matches: {}".format(pf(all_matches)))
        self.matches = all_matches
        self.currentMatches = True
        return self.matches

    def returnHashedMatches(self):
        sortedMatchkeys = sorted(self.returnMatches().keys())
        return sortedMatchkeys

    def returnMessages(self):
        if self.currentMessages:
            return self.messages
        all_matches = self.returnMatches()

        all_items = {key: [] for key in all_matches}
        item_div = self.soup.find(id='comment-box')
        item_table = item_div.findChild()
        for item_tr in item_table.childGenerator():
            if isinstance(item_tr, str): continue
            # old = item_tr

            current = {}
            gen = item_tr.children
            next(gen)
            tmp = next(gen)
            colour = tmp['style'][18:-1]
            colour = colour if len(colour) <= 7 else colour[0:7]
            # current['colour'] = colour
            if colour not in all_matches:
                print("Problem with colour {}, which is not in the matches {}".format(
                    colour, all_matches))
            # else:
            #     current['match'] = all_matches[colour]
            current['time'] = clearOfRandNandT(tmp.get_text()).replace(' ', '').strip()
            next(gen)
            tmp = next(gen)
            current['text'] = tmp.get_text().strip()

            all_items[colour].append(current)

        # print("{} ticker entries found, e.g. {}".format(len(all_items),
        #                                                 pf(current)))
        self.messages = {key: lst[::-1]
                         for key, lst in all_items.items()}
        self.currentMessages = True
        return self.messages
