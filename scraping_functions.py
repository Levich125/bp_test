import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re
from requests import get


class SportsBookScraper:
    """This class allows to grab only the visible data on page.
       For grabbing all data for different books selenium_scraper is used"""
    def __init__(self, soup, start_column_index=0):
        self.start_column_index = start_column_index  # for selenium processing, need other column names for data

        books_carousel = soup.find("ul", {'id': 'booksCarousel'})
        self.all_columns = [x.text.strip() for x in books_carousel.find_all('li')]
        self.tables = soup.find_all("div", {"class": "dateGroup"})  # table tags

    def construct_single_match_data(self, table_row_tag):
        """Construct 2-rows dataframe for single match, visible data only"""
        columns = self.all_columns[self.start_column_index: self.start_column_index + 10]
        if len(columns) < 10:  # always 10 books on page (excluding opener)
            columns = self.all_columns[-10:]
        columns = ['opener'] + columns

        match_id = table_row_tag.div.get('id', 'missing_id')
        match_url = table_row_tag.a.get('href', 'missing_url')
        match_time = table_row_tag.find("div", {"class": "el-div eventLine-time"}).text
        teams = [x.text for x in table_row_tag.find_all("span", {"class": "team-name"})]

        numbers = table_row_tag.find_all("div", {"id": re.compile(r"eventLine(?:Opener|Book)")})
        numbers = [int(x.text) if x.text else np.nan for x in numbers]  # Or 0 to keep dtype int? Or str will be fine?
        numbers_team1 = [x for x in numbers[::2]]
        numbers_team2 = [x for x in numbers[1::2]]

        d1 = pd.DataFrame([[match_time, match_url, teams[0]], [match_time, match_url, teams[1]]],
                          columns=['time', 'url', 'team'], index=[match_id] * 2)

        d2 = pd.DataFrame([numbers_team1, numbers_team2], columns=columns[:11], index=[match_id] * 2)
        return pd.concat([d1, d2], axis=1)

    def construct_whole_day_table(self, table_tag):
        """Construct the whole table. Concatenates rows from single matches"""
        table_rows = table_tag.find_all("div", {'id': re.compile(r"holder-\d+")})
        df = None

        for row in table_rows:
            df_row = self.construct_single_match_data(row)
            if df is None:
                df = df_row
            else:
                df = pd.concat([df, df_row], axis=0)

        dat = table_tag.find('div', {'class': 'date'})
        df.insert(loc=0, column='date', value=dat.text)  # date column added
        return df

    def main(self):
        out_list = []
        for table in self.tables:
            df = self.construct_whole_day_table(table)
            out_list.append(df)
        return out_list


if __name__ == "__main__":
    url = 'https://classic.sportsbookreview.com/betting-odds/nhl-hockey/?data=20170101'
    result = get(url)
    soup_param = BeautifulSoup(result.text, features="html.parser")
    scraper = SportsBookScraper(soup_param, 0)
    out = scraper.main()
    for i in out:
        print(i)
        print()
