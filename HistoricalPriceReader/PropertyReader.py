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
        self.num_properties = int(self.info.find(class_='fleft result-count').text.split(' of ')[0].split(' - ')[1])
        self.numPages = int(self.info.find(class_='paginate bg-muted').text.split(' ')[-1].split('\n')[0])

    def _getHTML(self, url):
        self.info = BeautifulSoup(requests.get(url).text, 'html.parser', from_encoding='utf-8')

    def _searchResultParser_old(self, info):
        res = []
        details = info.find_all('div', class_='soldDetails')
        for d in details:
            soldAddress = d.find(cass_='soldAddress')
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

    def _searchResultParser(self, info):
        res = []
        cell_addresses = info.find_all('td', class_ = 'browse-cell-address')
        sold_prices    = info.find_all('td', class_ = 'browse-cell-date')
        if len(cell_addresses) == len(sold_prices):
            details = tuple(zip(cell_addresses, sold_prices))
            for d in details:
                soldAddress = d[0]
                soldPrice   = d[1]
                price     = soldPrice.find('div', class_ = 'sold-prices-data sold-prices-data-price').text.strip() if soldPrice.find('div', class_ = 'sold-prices-data sold-prices-data-price') else ''
                room_attr = soldAddress.find('div', class_ = 'attributes').text.strip() if soldAddress.find('div', class_ = 'attributes') else ''
                address   = soldAddress.find('div', class_ = 'sold-prices-results-address').text.strip() if soldAddress.find('div', class_ = 'sold-prices-results-address') else ''
                soldDate  = soldPrice.find('div', class_ = 'sold-prices-data').text.strip() if soldPrice.find('div', class_ = 'sold-prices-data') else ''
                res.append(pd.DataFrame([[address, room_attr, price, soldDate]], columns = ['Address', 'Flat Type', 'Price', 'Sold Date']))
            results = pd.concat(res)
            return results
        else:
            return 'Error'

    def runUrl_old(self, url):
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

    def runUrl(self, url):
        self._getHTML(url)
        self._getNumInfo()
        all_results = []
        for i in range(self.numPages):
            new_url = url.split('?')[0] + '?pn=' + str(i+1)
            self._getHTML(new_url)
            all_results.append(self._searchResultParser(self.info))
        self.results = pd.concat(all_results)
        return self.results