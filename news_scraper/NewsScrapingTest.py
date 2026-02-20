import streamlit as st
import streamlit.components.v1 as components
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import fdds
import requests
import random


import re, html

def clean_display(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_PATH = os.path.join(BASE_DIR, "ndtv_cookies.json")  # file is beside NewsScrapingTest.py

def load_ndtv_cookies(session):
    with open(COOKIE_PATH, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", ".ndtv.com")
        path = c.get("path", "/")

        if name and value:
            session.cookies.set(name, value, domain=domain, path=path)


def scrape_page(url):
    domain = urlparse(url).netloc.lower()

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.ndtv.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    session = requests.Session()
    session.headers.update(headers)

    # ✅ LOAD NDTV COOKIES
    if "ndtv.com" in domain:
        load_ndtv_cookies(session)

        # warm-up request
        session.get("https://www.ndtv.com/", timeout=20)

    r = session.get(url, timeout=25, allow_redirects=True)
    return r.text



st.set_page_config(page_title="News Scraper", layout="wide")

st.title("📰 News Scraper Dashboard")

url = st.text_input("Enter News Article URL")


def id(url):
    """
    Detect Indian news source from article URL
    Returns: 'indiatoday', 'hindustantimes', 'zeenews', 'livemint', 'timesofindia' or None
    """
    domain = urlparse(url).netloc.lower()

    if "indiatoday.in" in domain:
        return 1

    if "hindustantimes.com" in domain:
        return 2

    if "zeenews.india.com" in domain or "zeenews.com" in domain:
        return 3

    if "livemint.com" in domain:
        return 4

    if "timesofindia.com" in domain or "timesofindia.indiatimes.com" in domain:
        return 5

    if "thehindu.com" in domain:
        return 6
    if "ndtv.com" in domain:
        return 7
    if "moneycontrol.com" in domain:
        return 8

    return 0


temp = 0
indToday = id(url)
if indToday == 1:
    temp = 1
index = id(url)

if st.button("Fetch News") and url:
    with st.spinner("Fetching article..."):
        htmlContent = scrape_page(url)
        soup = BeautifulSoup(htmlContent, "html.parser")

        title = fdds.get_Title(soup)
        title = clean_display(title)
        date = fdds.get_Date(soup)
        author = fdds.get_author(soup)
        desc = fdds.shor_description(soup)
        content = fdds.get_Context(index, soup)
        images = fdds.get_image(index, soup)
        social_links = fdds.get_social_media_Link(temp, soup)

    with st.expander(title):
        st.subheader(f"Title: {title}")
        st.markdown(f"**Date:** {date}")
        st.markdown(f"**Author:** {author}")
        st.markdown(f"**Description:** {desc}")

        st.subheader("Article Content")
        st.write(content)

        if images:
            st.subheader("🖼 Images")
            for img in images:
                if img["imgURL"]:
                    st.image(
                        img["imgURL"],
                        caption=img["imgTitle"] or img["imgAlt"],
                        use_column_width=True
                    )

        if social_links:
            st.subheader("📺 Embedded Media")
            for media in social_links:
                # st.write(media['link'])
                if media["link"]:

                    if media['source'] == 'instagram':
                        st.write("instagram")
                        components.html(
                            f"""
                                <blockquote class="instagram-media"
                                    data-instgrm-permalink="{media['link']}"
                                    data-instgrm-version="14">
                                </blockquote>
                                <script async src="//www.instagram.com/embed.js"></script>
                                """,
                            height=600
                        )
                    if media['source'] == 'reddit':
                        st.write("reddit")
                        components.html(
                            f"""
                                <blockquote class="reddit-embed-bq"
                                    style="height:500px"
                                    data-embed-height="500">
                                <a href="{media['link']}"></a>
                                </blockquote>
                                <script async src="https://embed.reddit.com/widgets.js" charset="UTF-8"></script>
                                """,
                            height=550
                        )
                    if media['source'] == 'twitter':
                        st.write("twitter")
                        components.html(
                            f"""
                                <blockquote class="twitter-tweet">
                                <a href="{media['link']}"></a>
                                </blockquote>
                                <script async src="https://platform.twitter.com/widgets.js"
                                        charset="utf-8"></script>
                                """,
                            height=550
                        )

                    if media['source'] == 'other':
                        st.write("other")
                        components.iframe(
                            src=media["link"],
                            width=400,
                            height=400,
                            scrolling=True
                        )