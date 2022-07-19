import logging
import re
from decimal import Decimal
from typing import Dict, List

import aiohttp
import asyncio
import chompjs
import pandas as pd
from bs4 import BeautifulSoup as BS

from bot.entities import Product, ProductOption
from bot.exceptions import ProductNotFoundError


HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

STATUS_OK = 200
STATUS_NOT_FOUND = 404

SELECTORS = {
    'title': 'h1',
    'description': 'div[itemprop="description"]',
    'image': '#image-main',
    'rating': '.rating',
    'reviews': '#goto-reviews',
    'options_block': '#product-options-wrapper',
    'availability': 'div.availability > span',
    'availability_item': '.stock-display',
    'availability_item_name': '.stock-warehouse',
    'additional_info': '#product-attribute-specs-table tbody > tr',
    'script': 'script',
    'span': 'span'
}

REGEXPS = {
    'script_1': re.compile('dataLayer.push'),
    'script_2': re.compile('document.observe'),
    'script_3': re.compile('var spConfig = new Product.Config'),
    'prices': r'(?<="options":).+(?=,"selected_option")',
    'titles': r'(?<="options":).+(?=}},"template")',
    'availabilities': r'(?<="subProductsAvailability":).+(?=}\);)',
    'current_product': r"(?<='currentProduct':)(.|\s)+(?=}\))",
    'availability_value': re.compile('color')
}

PARSER = 'lxml'


class Scraper:
    def __init__(self, url: str, session: aiohttp.ClientSession = None):
        self.url = url
        self.__session = session

    async def scrape_product(self) -> Product:
        """Scrape whole product data from page and return Product object."""
        if not self.__session:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                html = await self.get_html(session)
        else:
            html = await self.get_html(self.__session)

        soup = BS(html, PARSER)

        main_data = self.get_descriptive_data(soup)
        additional_info = self.get_data_from_additional_info(soup)
        product_options = self.get_product_options(soup)
        
        product = Product(
            id=None,
            brand=additional_info['brands'],
            description=main_data['description'],
            img=main_data['image'],
            title=main_data['title'],
            product_type=additional_info['product_type'],
            rating=main_data['rating'],
            reviews=main_data['reviews'],
            url=self.url,
            product_options=product_options
        )
        logging.info('Scraped product %s', product)
        return product

    async def get_html(self, session: aiohttp.ClientSession) -> str:
        """Helper func for sending request and getting page's html."""
        async with session.get(self.url) as response:
            status = response.status
            if status == STATUS_OK:
                return await response.text()
            elif status == STATUS_NOT_FOUND:
                raise ProductNotFoundError(
                    f'Product cannot be found on page {self.url}'
                )
            else:
                raise Exception(f'Request failed: {response}')
                

    def get_descriptive_data(self, soup: BS) -> Dict[str, str]:
        """Scrape descriptive data on page."""
        title = soup.select_one(SELECTORS['title'])
        description = soup.select_one(SELECTORS['description'])
        image = soup.select_one(SELECTORS['image'])
        rating = soup.select_one(SELECTORS['rating']).get('style')

        reviews_elem = soup.select_one(SELECTORS['reviews'])
        reviews = 0
        if reviews_elem:
            reviews = reviews_elem.get_text()
            reviews = int(re.search(r'\d+', reviews).group())

        return {
            'title': title.get_text(strip=True),
            'description': description.get_text(strip=True),
            'image': image.get('src'),
            'rating': 5 * (int(re.search(r'\d+', rating).group()) / 100),
            'reviews': reviews
        }

    def get_product_options(self, soup: BS) -> List[ProductOption]:
        """Scrape product options on page."""
        option_block = soup.select_one(SELECTORS['options_block'])
        if not option_block:
            product_option = self._get_one_product_option(soup)
            return [product_option]
        
        product_options = self._get_many_product_options(soup)
        return product_options

    def _get_one_product_option(self, soup: BS) -> ProductOption:
        """Scrape product page with only one option."""
        script_1 = soup.find_all(
            SELECTORS['script'], string=REGEXPS['script_1']
        )[1]
        price_and_title_text = script_1.get_text()
        
        current_product = chompjs.parse_js_object(re.search(
            REGEXPS['current_product'], price_and_title_text
        ).group())
        

        price = current_product['price']
        title = current_product['variant']
        availability_html = str(
            soup.select_one(SELECTORS['availability'])
        )

        return ProductOption(
            id=None,
            availability=self.parse_availability(availability_html),
            title=title,
            price=Decimal(price),
        )

    def _get_many_product_options(self, soup: BS) -> List[ProductOption]:
        """Scrape product page with many product options."""
        script_2 = soup.find_all(
            SELECTORS['script'], string=REGEXPS['script_2']
        )[-1]
        prices_text = script_2.get_text()

        script_3 = soup.find(SELECTORS['script'], string=REGEXPS['script_3'])
        titles_and_availability_text = script_3.get_text()

        prices = self.get_data_from_script_text(
            prices_text, REGEXPS['prices']
        )
        titles = self.get_data_from_script_text(
            titles_and_availability_text, REGEXPS['titles']
        )
        availabilities = self.get_data_from_script_text(
            titles_and_availability_text, REGEXPS['availabilities']
        )

        price_key = 'once_off_price'
        if self.has_sale_sticker(soup):
            price_key  = 'special_price' 

        keys = ['availability', 'label', price_key]
        joined_data = self.join_data(prices, titles, availabilities, keys)

        product_options = []
        for availability, title, price in joined_data:
            product_options.append(ProductOption(
                id=None,
                availability=self.parse_availability(availability),
                title=title,
                price=Decimal(price),
            ))
        return product_options

    @staticmethod    
    def get_data_from_script_text(text: str, regexp: str) -> List[Dict]:
        """Helper func for simplifying data extraction from given string."""
        string_data = re.search(regexp, text)
        if not string_data:
            return None
        return chompjs.parse_js_object(string_data.group())

    @staticmethod
    def has_sale_sticker(soup: BS) -> bool:
        return True if soup.select_one('span.sticker.sale') else False

    @staticmethod
    def join_data(prices: List[Dict], options: List[Dict], availabilities: List[Dict], keys: List[str]) -> List[List]:
        """"Join 3 dicts together and convert result to List[List]."""
        df1 = pd.DataFrame(prices)
        df2 = pd.DataFrame(options)
        df3 = pd.DataFrame(availabilities)

        merged_data = pd.merge(
            pd.merge(df1, df2, on='id'),
            df3,
            left_on='product_id', right_on='id'
        )
        result = merged_data[keys]
        return result.values.tolist()

    @staticmethod
    def parse_availability(availability_html: str) -> str:
        """Scrape availability_html and pretify scraped data."""
        soup = BS(availability_html, PARSER)

        rows_number = len(soup.select(SELECTORS['availability_item']))
        titles = tuple(map(
            lambda item: item.get_text(),
            soup.select(SELECTORS['availability_item_name'])
        ))

        if rows_number == 1:
            value = soup.find(
                SELECTORS['span'], style=REGEXPS['availability_value']
            ).span.get_text()

            return f'{", ".join(titles)}: {value}'

        elif rows_number > 1:
            values = tuple(map(
                lambda item: item.get_text(),
                soup.find_all(
                    SELECTORS['span'], style=REGEXPS['availability_value']
                )
            ))

            return '; '.join(
                [f'{titles[i]}: {values[i]}' for i in range(len(titles))]
            )
        
        return availability_html

    @staticmethod
    def get_data_from_additional_info(soup: BS) -> Dict:
        """Scrape data from additional info table on product page."""
        def to_snake_case(value: str) -> str:
            return '_'.join(value.lower().split())

        text_to_find = ('Brands', 'Product Type')
        keys = tuple(map(to_snake_case, text_to_find))

        trs = tuple(filter(
            lambda tag: tag.th.get_text(strip=True) in text_to_find,
            soup.select(SELECTORS['additional_info'])
        ))

        return {
            keys[i]: trs[i].td.get_text(strip=True) for i in range(len(trs))
        }


if __name__ == '__main__':
    url1 = 'https://www.petheaven.co.za/dogs/dog-food/acana/acana-pacific-pilchard-dog-food.html'
    url2 = 'https://www.petheaven.co.za/other-pets/birds/bird-treats/marlton-s-fruit-nut-parrot-food-mix.html'
    url3 = 'https://www.petheaven.co.za/other-pets/small-pets/small-pet-habitats/wagworld-nap-sack-fleece-pet-bed-navy.html'
    url4 = 'https://www.petheaven.co.za/beeztees-sumo-halterino-dumbell-dog-toy.html'
    url5 = 'https://www.petheaven.co.za/dogs/dog-clothing/jackets/dog-s-life-summer-raincoat-spots-black.html'
    url6 = 'https://www.petheaven.co.za/cats/cat-treats/orijen/orijen-6-fish-freeze-dried-cat-treats.html'
    scraper = Scraper(url5)
    asyncio.run(scraper.scrape_product())