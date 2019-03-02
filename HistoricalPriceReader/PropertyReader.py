import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd


class PropertySoldPriceReader():
    '''
    Read historical property prices
    '''

    def __init__(self, **kwargs):
        self.developement = kwargs.pop('development', None)
        self.reconfig(**kwargs)

    def reconfig(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _getNumInfo(self):
        self.num_properties = int(self.info.find(id='resultcount').text.split('+')[0])
        self.numPages = int(self.info.find(class_='pagenavigation pagecount').text.split('of ')[-1])

    def _getHTML(self, url):
        self.info = BeautifulSoup(requests.get(url).text, 'html.parser', from_encoding='utf-8')

    def _searchResultParser(self, info):
        res = []
        details = info.find_all('div', class_='soldDetails')
        for d in details:
            soldAddress = d.find(class_='soldAddress')
            soldHist = d.find_all('tr')
            for unit in soldHist:
                df_parsed = self.parseOneUnit(unit)
                df_parsed.index = soldAddress
                df_parsed.index.name = 'Property'
                res.append(df_parsed)
        results = pd.concat(res)
        return results

    @staticmethod
    def parseOneUnit(unit_html):
        soldPrice = float(unit_html.find(class_='soldPrice').text[1:].replace(',', ''))
        soldType = unit_html.find(class_='soldType').text
        soldDate = datetime.datetime.strptime(unit_html.find(class_='soldDate').text, '%d %b %Y')
        return pd.DataFrame([[soldPrice, soldType, soldDate]], columns=['soldPrice', 'soldType', 'soldDate'])

    def runUrl(self, url):
        self._getHTML(url)
        self._getNumInfo()
        all_results = []
        for i in range(self.numPages):
            new_url = url.split('&index=')[0] + '&index=' + str(i * 25)
            self._getHTML(new_url)
            all_results.append(self._searchResultParser(self.info))
        self.results = pd.concat(all_results)
        self.results.reset_index(inplace=True)
        self.results.set_index(['Property', 'soldDate'], inplace=True)
        return self.results