# -----------------------------------------------
# macaulay_scraper.py
# -----------------------------------------------
# This script extracts the highest-rated adult photo for each bird species
# from the Macaulay Library using Playwright. The result is mapped back to 
# the original DataFrame and saved to a CSV file.
#
# Dependencies:
# - pandas
# - numpy
# - playwright (install with `pip install playwright && playwright install`)
#
# Author: [Your Name]
# Date: [YYYY-MM-DD]
# -----------------------------------------------

import numpy as np
import pandas as pd
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# -----------------------------------------------
# Load dataset and extract unique species codes
# -----------------------------------------------
df = pd.read_csv("bird_data_revised.csv")
taxon_list = df['SPECIES_CODE'].unique().tolist()

# -----------------------------------------------
# Scrape the first photo link for a given taxon code
# -----------------------------------------------
async def get_first_macaulay_link(taxon_code):
    """
    Given a taxon code (e.g., 'norcar'), fetches the first high-quality
    adult photo URL from the Macaulay Library.
    """
    url = (
        f"https://media.ebird.org/catalog?birdOnly=true"
        f"&taxonCode={taxon_code}&age=adult&sort=rating_rank_desc&mediaType=photo"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for silent mode
        page = await browser.new_page()
        print(f"🔍 Opening: {url}")
        await page.goto(url, wait_until="networkidle")

        try:
            # Wait until a link to an image asset appears
            await page.wait_for_selector("a[href*='macaulaylibrary.org/asset']", timeout=15000)
            element = await page.query_selector("a[href*='macaulaylibrary.org/asset']")
            href = await element.get_attribute("href") if element else None

            if href:
                # Strip query params to get the clean URL
                clean_href = urlparse(href)._replace(query="").geturl()
                print(f"✅ Found clean link: {clean_href}")
                return clean_href
            else:
                print("⚠️ Element found but no href.")
                return None

        except Exception as e:
            print(f"❌ Error for {taxon_code}: {e}")
            return None
        finally:
            await browser.close()

# -----------------------------------------------
# Process a list of taxon codes and collect results
# -----------------------------------------------
async def get_links_for_taxa(taxon_codes):
    """
    Loops through a list of taxon codes and returns a dictionary
    mapping each code to its Macaulay Library image URL.
    """
    results = {}
    for code in taxon_codes:
        link = await get_first_macaulay_link(code)
        results[code] = link
    return results

# -----------------------------------------------
# Run the scraper and update the DataFrame
# -----------------------------------------------
results = asyncio.run(get_links_for_taxa(taxon_list))

# Map image links to the DataFrame and save updated CSV
df["MACAULAY_LINK"] = df["SPECIES_CODE"].map(results).fillna("No image found")
df.to_csv('bird_data_revised.csv', index=False)
