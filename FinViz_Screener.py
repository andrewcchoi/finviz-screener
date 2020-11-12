import datetime as dt
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def screener(ticker=None):
    """filter for specific stock, save screenshots of charts, and crop charts"""

    def fetch(xurl, xparser="html.parser"):
        """retrieve html from website"""
        driver.get(xurl)
        return BeautifulSoup(driver.page_source, xparser)

    # setting variables
    beg_time = dt.datetime.now()
    dt_now = dt.datetime.now()
    fn_now = (
        str(pd.to_datetime(dt_now).year)
        + f"{pd.to_datetime(dt_now).month:02d}"
        + f"{pd.to_datetime(dt_now).day:02}"
    )
    url_base = f"https://finviz.com"
    url_path = f"screener.ashx?v=111&f=sh_avgvol_o100,sh_curvol_o100,sh_price_u2,sh_relvol_o1.5"
    url = urljoin(url_base, url_path)
    list_pgs = [url_path]
    parser = ["html.parser", "lxml"]
    dict_tickers = {}

    # verify directory and create new folder
    Path(rf"./screenshots/screener_{fn_now}/crop").mkdir(parents=True, exist_ok=True)

    try:
        if ticker is None:
            # start chrome hidden
            chrome_options = Options()
            chrome_options.add_argument("headless")
            driver = webdriver.Chrome(
                ChromeDriverManager().install(), options=chrome_options
            )
            soup = fetch(url, parser[1])

            # store url of all pages from filtered screeners
            list_pgs.extend(
                [el["href"] for el in soup.find_all(class_="screener-pages")]
            )
            # add ticker and url from filtered list
            for i, _ in enumerate(list_pgs, start=1):
                for el in soup.find_all("a", class_="screener-link-primary"):
                    dict_tickers[el.get_text()] = urljoin(url_base, el["href"])

                if i < len(list_pgs):
                    soup = fetch(urljoin(url_base, list_pgs[i]), parser[1])

            driver.quit()

        else:
            dict_tickers.update(
                {ticker: f"https://finviz.com/quote.ashx?t={ticker}&ty=c&p=d&b=1"}
            )

        # set download directory
        prefs = {
            "download_restrictions": 3,
            "download.default_directory": "/dev/null",
        }

        # setting Chrome settings to disable information bar, start maximized, execute driver, go to predetermined url
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options
        )

        for key, value in dict_tickers.items():
            # loop through the list of tickers, save screenshots and crop
            fetch(value, parser[1])

            print(key, value, sep=": ")
            driver.save_screenshot(
                rf"./screenshots/screener_{fn_now}/screener_{fn_now}_{key}.png"
            )
            element = driver.find_element_by_xpath('//*[@id="chart0"]')
            left = element.location["x"] + 140
            top = element.location["y"] + 80
            right = (left * 2) + element.size["width"] - 350  # 1500
            bottom = (top * 2) + element.size["height"] - 265  # 700~780
            im = Image.open(
                rf"./screenshots/screener_{fn_now}/screener_{fn_now}_{key}.png"
            )
            im = im.crop((int(left), int(top), int(right), int(bottom)))
            im.save(
                rf"./screenshots/screener_{fn_now}/crop/cropped_screener_{fn_now}_{key}.png"
            )

    except Exception as e:
        print(e)

    finally:
        driver.quit()
        end_time = dt.datetime.now()
        print(
            f"Beg: {beg_time}",
            f"End: {end_time}",
            f"Dur: {end_time - beg_time}",
            sep="\n",
        )


stock_ticker = input("Enter Ticker: ")

if stock_ticker == "":
    stock_ticker = None

screener(stock_ticker)
