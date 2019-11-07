from functools import reduce
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd

from scraping_functions import SportsBookScraper


def collect_merged_tables(url):
    """Uses selenium to browse through all books since there is no data on the page for those that
       are not currently visible"""
    browser = webdriver.Firefox()
    browser.get(url)

    scraper_outputs = []

    books_idx = 0  # controls column names
    while 1:
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        scraper = SportsBookScraper(soup, books_idx)
        out = scraper.main()
        scraper_outputs.append(out)  # all tables, visible parts
        books_idx += 10

        nxt = soup.find('a', {'class': 'next'})
        # print(nxt['class'])
        if len(nxt['class']) > 1:  # ['next', 'carousel-button-disabled'] - got all we need
            break

        nextpage = browser.find_element_by_class_name('next')
        nextpage.click()  # load further data
        sleep(2)  # so the new results will be ready

    tables_number = len(scraper_outputs[0])
    out_tables = []
    for i in range(tables_number):
        merged = reduce(lambda x, y: pd.merge(x.reset_index(), y.reset_index()),
                        [x[i] for x in scraper_outputs])  # merge data on different books into one table
        try:
            del merged['level_0']
        except KeyError:
            pass
        out_tables.append(merged)
    browser.quit()
    return out_tables


if __name__ == '__main__':
    page_url = 'https://classic.sportsbookreview.com/betting-odds/nhl-hockey/?data=20170101'
    tables = collect_merged_tables(page_url)
    print(tables[1])
