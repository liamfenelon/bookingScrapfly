import asyncio
from collections import defaultdict
import json
from pathlib import Path
import re
from typing import List, Optional
from urllib.parse import urlencode
from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
from parsel import Selector

scrapfly = ScrapflyClient(key="scp-live-2958dd757bfd49aeaa7f92941912a401")


async def request_hotels_page(
    query,
    checkin: str = "",
    checkout: str = "",
    number_of_rooms=1,
    offset: int = 0,
):
    """scrapes a single hotel search page of booking.com"""
    checkin_year, checking_month, checking_day = checkin.split("-") if checkin else "", "", ""
    checkout_year, checkout_month, checkout_day = checkout.split("-") if checkout else "", "", ""

    url = "https://www.booking.com/searchresults.html"
    url += "?" + urlencode(
        {
            "ss": query,
            "checkin_year": checkin_year,
            "checkin_month": checking_month,
            "checkin_monthday": checking_day,
            "checkout_year": checkout_year,
            "checkout_month": checkout_month,
            "checkout_monthday": checkout_day,
            "no_rooms": number_of_rooms,
            "offset": offset,
        }
    )
    return await scrapfly.async_scrape(ScrapeConfig(url, country="US"))


def parse_search_total_results(html: str):
    sel = Selector(text=html)
    # parse total amount of pages from heading1 text:
    # e.g. "London: 1,232 properties found"
    total_results = int(sel.css("h1").re("([\d,]+) properties found")[0].replace(",", ""))
    return total_results


def parse_search_hotels(html: str):
    sel = Selector(text=html)

    hotel_previews = {}
    for hotel_box in sel.xpath('//div[@data-testid="property-card"]'):
        url = hotel_box.xpath('.//h3/a[@data-testid="title-link"]/@href').get("").split("?")[0]
        hotel_previews[url] = {
            "name": hotel_box.xpath('.//h3/a[@data-testid="title-link"]/div/text()').get(""),
            "location": hotel_box.xpath('.//span[@data-testid="address"]/text()').get(""),
            "score": hotel_box.xpath('.//div[@data-testid="review-score"]/div/text()').get(""),
            "review_count": hotel_box.xpath('.//div[@data-testid="review-score"]/div[2]/div[2]/text()').get(""),
            "stars": len(hotel_box.xpath('.//div[@data-testid="rating-stars"]/span').getall()),
            "image": hotel_box.xpath('.//img[@data-testid="image"]/@src').get(),
        }
    return hotel_previews


async def scrape_search(
    query,
    checkin: str = "",
    checkout: str = "",
    number_of_rooms=1,
    max_results: Optional[int] = None,
):
    first_page = await request_hotels_page(
        query=query, checkin=checkin, checkout=checkout, number_of_rooms=number_of_rooms
    )
    hotel_previews = parse_search_hotels(first_page.content)
    total_results = parse_search_total_results(first_page.content)
    if max_results and total_results > max_results:
        total_results = max_results
    other_pages = await asyncio.gather(
        *[
            request_hotels_page(
                query=query,
                checkin=checkin,
                checkout=checkout,
                number_of_rooms=number_of_rooms,
                offset=offset,
            )
            for offset in range(25, total_results, 25)
        ]
    )
    for result in other_pages:
        hotel_previews.update(parse_search_hotels(result.content))
    return hotel_previews

def getCountiesIreland():
    with open("resources/NorthernIreland.txt", "r") as f:
        counties: list = f.read().splitlines()
    f.close()
    return counties

async def run():
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    counties = getCountiesIreland()
    for county in counties:
        result_search = await scrape_search(county, checkin="", checkout="")
        out.joinpath(county + ".json").write_text(json.dumps(result_search, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())