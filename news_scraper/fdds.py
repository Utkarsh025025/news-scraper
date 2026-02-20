import json
from bs4 import BeautifulSoup, NavigableString,Tag
import re


def get_date_in_json(soup):
    json_ld_scripts = soup.find_all("script", type="application/ld+json")

    for script in json_ld_scripts:
        raw = script.string
        if not raw:
            continue

        # remove illegal control characters that break json.loads (Moneycontrol issue)
        raw = re.sub(r'[\x00-\x1F\x7F]', '', raw).strip()

        try:
            data = json.loads(raw)
        except Exception:
            continue

        # JSON-LD can be dict OR list
        items = []
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = [x for x in data if isinstance(x, dict)]
        else:
            continue

        for d in items:
            if d.get("@type") in ("NewsArticle", "Article", "ReportageNewsArticle"):
                dp = d.get("datePublished") or d.get("dateCreated") or d.get("dateModified")
                if dp:
                    return str(dp)[:10]

    return None



def get_Title(soup):
    import re

    def normalize(t):
        if not t:
            return t
        # fix broken encoding ONLY if it exists
        try:
            if any(x in t for x in ("â", "Â", "�")):
                t = t.encode("latin1").decode("utf-8")
        except:
            pass
        return re.sub(r"\s+", " ", t).strip()

    og = soup.find('meta', {"property": "og:title"})
    if og and og.get("content"):
        return normalize(og["content"])

    h1 = soup.find("h1")
    return normalize(h1.text) if h1 else "Not Found"


def get_author(soup):
    # INDIA TODAY

    author_divs = soup.find_all("div", class_="authdetaisl")
    if author_divs:
        return author_divs[0].get_text(strip=True)

    # ZEE NEWS

    zee_author = soup.find("span", class_="aaticleauthor_name")
    if zee_author:
        text = zee_author.get_text()
        return text

    # HINDUSTAN TIMES

    small = soup.find("small")
    if small:
        return small.get_text(strip=True)

    # livemint

    mint_author = soup.find("meta", {"name": "author"})
    if mint_author:
        return mint_author.get("content")

    # Times of india

    toi_author = soup.select_one('a[href*="toireporter"]')
    if toi_author:
        return toi_author.get_text(strip=True)

    # The hindu
    hindu_author = soup.find("div" , class_ = "author")
    if hindu_author:
        return hindu_author.get_text(strip=True)


    # ✅ NDTV
    ndtv_author = soup.select_one('meta[name="author"]')
    if ndtv_author and ndtv_author.get("content"):
        return ndtv_author["content"].strip()

    # 🔥 NDTV Entertainment fallback (Written by)
    author_tag = soup.select_one("a.pst-by_lnk")
    if author_tag:
        return author_tag.get_text(strip=True)

    # Money Control
    moneycontrol_author = soup.find("div" , class_ = "article_author")
    if moneycontrol_author:
        return moneycontrol_author.get_text(strip=True)

    return "Not Found"

def get_Date(soup):
    meta_date = soup.find("meta", {"property": "article:published_time"})
    if meta_date:
        date = meta_date.get("content", "")[:10]
    else:
        date = get_date_in_json(soup)
    return date


def shor_description(soup):
    short_desc = soup.find('meta', {"name": "description"})
    if short_desc:
        return short_desc["content"].strip()
    else:
        return "Not Found"


def get_Context(id, soup):
    if id == 0:
        content = []
        for p in soup.find_all('p'):

            text = p.get_text()
            if text:
                content.append(text)

        article_text = "\n".join(content)
        return article_text

    content = []
    if id == 1:
        for p in soup.find_all("p"):
            for child in p.contents:

                # stop when
                if getattr(child, "name", None) == "div" and "end_story" in child.get("class", []):
                    return "\n".join(content)

                # plain text
                if isinstance(child, NavigableString):
                    text = child.strip()
                    if text:
                        content.append(text)
                # anchor / strong text
                elif child.name in ["a", "strong", "span"]:
                    text = child.get_text(strip=True)
                    if text:
                        content.append(text)
        return "\n".join(content)
    if id == 2:
        article = soup.find_all(["div", "p"], class_=["content", "blogTitle liveBlogHdg"])
        if article:
            for p in article:

                # Case 1: Read More block
                if p.find("strong") and "Read More" in p.get_text():
                    None
                    # Case 2: Normal paragraph
                if p.find('i'):
                    None
                if p.find('h2') and p.find('a'):
                    text = (p.find('p')).get_text()
                    if text:
                        content.append(text)
                else:
                    text = p.get_text(strip=True)
                    if text:
                        content.append(text)

            return "\n".join(content)
        else:
            article = soup.find_all(["div", "p"], id="fullIntroContent")
            if article:
                for p in article:

                    # Case 1: Read More block
                    if p.find("strong") and "Read More" in p.get_text():
                        None
                        # Case 2: Normal paragrap
                    if p.find('i'):
                        None
                    if p.find('h2') and p.find('a'):
                        text = (p.find('p')).get_text()
                        if text:
                            content.append(text)
                    else:
                        text = p.get_text(strip=True)
                        if text:
                            content.append(text)

                return "\n".join(content)

    if id == 3:
        article = soup.find(id="fullArticle")
        s = str(article)
        soup1 = BeautifulSoup(s, 'html.parser')
        container = soup1.find('div', id='fullArticle')
        cleaned_lines = []
        if container:

            for junk in container.find_all(['script', 'iframe', 'div', 'ins'],
                                           class_=['ads-box-300x250', 'recommended_widget', 'googlePopUp', 'mb-3',
                                                   'ads-placeholder-internal']):
                junk.decompose()

            # 3. Get all text with a double newline separator to keep it readable
            # strip=True removes leading/trailing whitespace from each chunk
            lines = container.get_text(separator="\n\n", strip=True).split('\n\n')

            # 4. Filter out the specific lines you mentioned
            for line in lines:
                # Skip the Zee News CTA
                if "Add Zee News as a Preferred Source" in line:
                    continue
                # Skip "Also Read" links
                if line.startswith("Also Read-"):
                    continue
                # Skip Agency credits
                if any(credit in line for credit in ["(with IANS inputs)", "(With ANI inputs)"]):
                    continue

                cleaned_lines.append(line)
        else:
            print("Article container not found.")
        return "\n".join(cleaned_lines)

    if id == 4:
        cont = soup.find_all("div", class_="storyParagraph")
        content = []
        for p in cont:
            text = p.get_text()
            content.append(text + "\n")
        return "\n".join(content)

    if id == 5:
        JUNK = re.compile(
            r"(Advertisement|Go Ad Free Now|Tired of too many ads|SUBSCRIBE\s+NOW)",
            re.I
        )
        ALSO_READ = re.compile(r"Also read\s*\|.*?$", re.I)

        def clean(t: str) -> str:
            if not t:
                return ""
            if "â" in t or "Â" in t:
                try:
                    t = t.encode("latin1").decode("utf-8")
                except Exception:
                    pass
            t = re.sub(r"\s+", " ", t).strip()
            return t

        def is_toi_break(tag: Tag) -> bool:
            # TOI uses spans like: <span class="id-r-component br" data-pos="1"></span>
            if not isinstance(tag, Tag):
                return False
            if tag.name != "span":
                return False
            cls = tag.get("class") or []
            cls = [c.lower() for c in cls]
            return ("br" in cls) and ("id-r-component" in cls)

        def finalize_paras(paras):
            out, seen = [], set()
            for p in paras:
                p = clean(p)
                if not p:
                    continue
                if JUNK.search(p):
                    continue
                p = ALSO_READ.sub("", p).strip()
                if not p:
                    continue
                key = p.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(p)
            return "\n\n".join(out).strip()

        body = soup.select_one('div[data-articlebody="1"]')
        if body:
            paras = []
            buf = []

            # Walk in DOM order; build paragraph text with spaces
            for node in body.descendants:
                if isinstance(node, Tag):
                    # treat TOI break spans as PARAGRAPH separators
                    if is_toi_break(node):
                        paragraph = clean(" ".join(buf))
                        if paragraph:
                            paras.append(paragraph)
                        buf = []
                        continue

                    # If TOI uses real <p> tags on some pages, also break paragraphs here
                    if node.name == "p":
                        # start of <p> does nothing; we flush when </p> reached using its text
                        # to avoid double text, skip collecting inside <p> here
                        # (we'll handle <p> separately below)
                        pass

                # collect actual visible text pieces
                if isinstance(node, NavigableString):
                    txt = clean(str(node))
                    if txt:
                        buf.append(txt)

            # flush last buffer
            last = clean(" ".join(buf))
            if last:
                paras.append(last)

            # If page has proper <p> tags, prefer those (they preserve paragraphs naturally)
            p_tags = body.find_all("p")
            if p_tags:
                paras = []
                for p in p_tags:
                    txt = clean(p.get_text(" ", strip=True))
                    if txt:
                        paras.append(txt)

            result = finalize_paras(paras)
            if result:
                return result

        # JSON-LD fallback (keeps as one block but still usable)
        best_body = ""
        for sc in soup.find_all("script", type="application/ld+json"):
            raw = (sc.string or "").strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue

            items = [data] if isinstance(data, dict) else [x for x in data if isinstance(x, dict)] if isinstance(data,
                                                                                                                 list) else []
            for d in items:
                if d.get("@type") in ("NewsArticle", "Article", "ReportageNewsArticle"):
                    ab = d.get("articleBody") or ""
                    if isinstance(ab, str) and len(ab) > len(best_body):
                        best_body = ab

        if best_body:
            best_body = clean(best_body)
            best_body = re.sub(r"\.(?=[A-Z])", ". ", best_body)  # fix missing space after period
            best_body = ALSO_READ.sub("", best_body).strip()
            if not JUNK.search(best_body):
                return best_body

        return "Article content not found"

            # other sites (your existing/default logic)
        content = []
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                content.append(text)
        return "\n\n".join(content)

    if id == 6:
        article = soup.find("div", class_="schemaDiv")
        if not article:
            return "Not Found"

        # remove obvious junk blocks inside article body
        for bad in article.select("div.article-ad, div.inline-embed, div#artmeterpv, p.caption"):
            bad.decompose()

        content = []
        for p in article.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                content.append(text)

        return "\n\n".join(content) if content else "Not Found"

    if id == 7:
        article = soup.find("div", class_="Art-exp_wr")
        if not article:
            return "Not Found"

        # remove obvious junk blocks inside article body
        for bad in article.select("div.article-ad, div.inline-embed, div#artmeterpv, p.caption"):
            bad.decompose()

        content = []
        for p in article.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                content.append(text)

        return "\n\n".join(content) if content else "Not Found"
    
    if id == 8:
        article = soup.find("div", class_="content_wrapper arti-flow")
        if not article:
            return "Not Found"

        # remove obvious junk blocks inside article body
        for bad in article.select("div.article-ad, div.inline-embed, div#artmeterpv, p.caption"):
            bad.decompose()

        content = []
        for p in article.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                content.append(text)

        return "\n\n".join(content) if content else "Not Found"



def get_image(id, soup):
    img_list = []
    try:
        img_main_url = (soup.find("meta", {"property": "og:image"}))['content']

        if img_main_url:
            img_url = img_main_url.split("/")[-1].split("?")[0]
            img_tag = soup.find("img", src=lambda x: x and img_url in x)
            if img_tag:
                img_list.append({
                    "imgURL": img_tag.get('src') or "",
                    "imgTitle": img_tag.get('title') or "",
                    "imgAlt": img_tag.get('alt') or "",
                    "imgHeight": img_tag.get('height') or "",
                    "imgWidth": img_tag.get('width') or "", })
    except:
        None
    if id == 1:
        try:
            img_all = soup.find_all('div', class_="itgimage")

            if img_all:
                for item in img_all:
                    img_list.append({
                        "imgURL": item.img.get('src') or "",
                        "imgTitle": item.img.get('title') or "",
                        "imgAlt": item.img.get('alt') or "",
                        "imgHeight": item.img.get('height') or "",
                        "imgWidth": item.img.get('width') or "", })
            return img_list
        except:
            None
    if id == 2:
        try:
            img_all = soup.find_all(class_='artImage')
            if img_all:
                for item in img_all:
                    img_list.append({
                        "imgURL": item.img.get('data-src') or item.img.get('data') or "",
                        "imgTitle": item.img.get('title') or "",
                        "imgAlt": item.img.get('alt') or ""})
            return img_list
        except:
            None
    if id == 3:
        try:
            img_all = soup.find_all("div", class_="photoimg_container")
            if img_all:
                for item in img_all:
                    img_list.append({
                        "imgURL": item.img.get('data-src') or item.img.get('data') or "",
                        "imgTitle": item.img.get('title') or "",
                        "imgAlt": item.img.get('alt') or ""})
            return img_list
        except:
            None

    if id == 4:
        try:
            img = soup.select_one("figure img")

            if not img:
                return []

            img_url = img.get("src") or img.get("data-src") or ""

            if not img_url:
                return []

            return [{
                "imgURL": img_url,
                "imgTitle": img.get("title") or "",
                "imgAlt": img.get("alt") or "",
                "imgHeight": img.get("height") or "",
                "imgWidth": img.get("width") or ""
            }]

        except Exception:
            return []

    if id == 5:
        try:
            img_list = []
            seen_urls = set()

            # STRICTLY article body
            article_body = soup.find("div", {"data-articlebody": "1"})
            if not article_body:
                return []

            imgs = article_body.find_all("img")

            for img in imgs:
                # ✅ 1) Skip banner/ad blocks by parent containers (TOI specific)
                if img.find_parent("div", {"data-type": "in_view"}):
                    continue

                # ✅ 2) Skip if alt/title indicates banner
                alt = (img.get("alt") or "").strip().lower()
                title = (img.get("title") or "").strip().lower()
                if "banner" in alt or "banner" in title:
                    continue

                # ✅ 3) Skip if image is inside an outgoing ad link (bookmyshow etc.)
                a = img.find_parent("a", href=True)
                if a and any(x in a["href"].lower() for x in ["bookmyshow", "utm_", "campaign"]):
                    continue

                img_url = (
                        img.get("data-src")
                        or img.get("data-original")
                        or img.get("src")
                )

                if not img_url:
                    continue

                # remove thumbnails, icons, sprites, ads
                if any(x in img_url.lower() for x in ["sprite", "logo", "icon", "ads"]):
                    continue

                # avoid duplicates
                if img_url in seen_urls:
                    continue
                seen_urls.add(img_url)

                img_list.append({
                    "imgURL": img_url,
                    "imgTitle": img.get("title") or "",
                    "imgAlt": img.get("alt") or "",
                    "imgHeight": img.get("height") or "",
                    "imgWidth": img.get("width") or ""
                })

            return img_list

        except Exception:
            return []

    if id == 6:
        try:
            img_list = []
            seen = set()

            # Hindu main article image block
            blocks = soup.select("div.article-picture")

            for block in blocks:
                # 1) try <img class="lead-img" ...>
                for img in block.select("img.lead-img, img"):
                    url = (
                            img.get("data-original")
                            or img.get("data-src")
                            or img.get("src")
                            or ""
                    ).strip()

                    # if still placeholder, try srcset from closest <picture>
                    if (not url) or ("1x1_spacer" in url):
                        pic = img.find_parent("picture")
                        if pic:
                            src = pic.find("source", attrs={"srcset": True})
                            if src:
                                # take first URL in srcset
                                url = src["srcset"].split(",")[0].strip().split(" ")[0]

                    if not url or "1x1_spacer" in url:
                        continue

                    # dedupe
                    if url in seen:
                        continue
                    seen.add(url)

                    img_list.append({
                        "imgURL": url,
                        "imgTitle": img.get("title") or "",
                        "imgAlt": img.get("alt") or "",
                        "imgHeight": img.get("height") or "",
                        "imgWidth": img.get("width") or "",
                    })

            return img_list

        except Exception as e:
            print("Hindu image error:", e)
            return []

    if id == 7:
        try:
            img_list = []
            seen = set()   # to avoid duplicates

            img_all = soup.find_all("div", class_="ins_instory_dv")

            for item in img_all:
                img = item.find("img")
                if not img:
                    continue

                img_url = img.get("src") or ""
                if not img_url:
                    continue

                # remove duplicate images
                if img_url in seen:
                    continue
                seen.add(img_url)

                img_list.append({
                    "imgURL": img_url,
                    "imgTitle": img.get("title") or "",
                    "imgAlt": img.get("alt") or ""
                })

            return img_list

        except Exception as e:
            print("Image scraping error:", e)
            return []
        
    if id == 8:
        try:
            img_all = soup.find_all("div", class_="article_image")
            if img_all:
                for item in img_all:
                    img_list.append({
                        "imgURL": item.img.get('data-src') or item.img.get('data') or "",
                        "imgTitle": item.img.get('title') or "",
                        "imgAlt": item.img.get('alt') or ""})
            return img_list
        except:
            None



def get_social_media_Link(id, soup):
    list_of_links = []
    if id == 1:
        listOfArticles = soup.find_all('article')
        if listOfArticles:
            for article in listOfArticles:
                fram = article.find(['iframe'])
                if fram:
                    list_of_links.append({
                        "link": fram.get('src') or "",
                        "source": "other"})
        return list_of_links
    if id == 0:
        listofReddit = soup.find_all("blockquote", class_="reddit-embed-bq")
        if listofReddit:
            for post in listofReddit:
                link = post.a.get("href")
                if link:
                    list_of_links.append({
                        "link": link or "",
                        "source": "reddit"})

        listofinstagram = soup.find_all('blockquote', class_="instagram-media")
        if listofinstagram:
            for post in listofinstagram:
                link = post.get("data-instgrm-permalink")
                if link:
                    list_of_links.append({
                        "link": link or "",
                        "source": "instagram"})
        listofTweet = soup.find_all('div', class_='ht-twitter-embed')
        if listofTweet:
            for post in listofTweet:
                link = post.get("data-twitter-src")
                if link:
                    list_of_links.append({
                        "link": link or "",
                        "source": "twitter"})

        listofTweetZee = soup.find_all('blockquote', class_="twitter-tweet")
        if listofTweetZee:
            for post in listofTweetZee:
                anchors = post.find_all('a')
                for a in anchors:
                    href = a.get('href')
                    if href and href.startswith("https://twitter.com/"):
                        list_of_links.append({
                            "link": href,
                            "source": "twitter"
                        })

        fb_links = re.findall(
            r'https://www\.facebook\.com/plugins[^"\']+',
            str(soup)
        )

        fb_links = [
            {"link": link, "source": "other"}
            for link in set(fb_links)
        ]
        list_of_links.extend(fb_links)

        return list_of_links





