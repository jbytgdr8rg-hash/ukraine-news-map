#!/usr/bin/env python3
"""Daily Google News RSS ingestion; location-based conservative classification."""
import datetime as dt
import email.utils
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data.json'
NOW = dt.datetime.now(dt.timezone.utc)
# Broad locations deliberately represent cities/regions, not precise incident sites.
PLACES = [
    ('キーウ', ['kyiv','kiev','キーウ'], 50.4501,30.5234),
    ('ハルキウ', ['kharkiv','kharkov','ハルキウ'],49.9935,36.2304),
    ('リヴィウ', ['lviv','リヴィウ'],49.8397,24.0297),
    ('オデーサ', ['odesa','odessa','オデーサ'],46.4825,30.7233),
    ('ドニプロ', ['dnipro','dnipropetrovsk','ドニプロ'],48.4647,35.0462),
    ('ザポリージャ', ['zaporizhzhia','zaporizhia','ザポリージャ'],47.8388,35.1396),
    ('ヘルソン', ['kherson','ヘルソン'],46.6354,32.6169),
    ('スーミ', ['sumy','スーミ'],50.9077,34.7981),
    ('ドネツク', ['donetsk','ドネツク'],48.0159,37.8029),
    ('クリミア橋', ['kerch bridge','crimea bridge','crimean bridge'],45.30,36.51),
    ('ポーランド南東部', ['poland','polish','ポーランド'],50.58,22.54),
    ('モルドバ', ['moldova','moldovan','モルドバ'],47.01,28.86),
    ('エストニア', ['estonia','estonian','エストニア'],59.437,24.7536),
    ('モスクワ', ['moscow','モスクワ'],55.7558,37.6173),
    ('ベルリン', ['berlin','ベルリン'],52.52,13.405),
    ('ブリュッセル', ['brussels','ブリュッセル'],50.8503,4.3517),
]
QUERIES = ['Ukraine Russia strikes missiles drones when:3d', 'Ukraine Russia NATO Poland border when:3d', 'Ukraine Russia peace talks diplomacy when:3d']

def parse_date(s):
    try:
        v=email.utils.parsedate_to_datetime(s)
        return v.astimezone(dt.timezone.utc)
    except Exception:
        return NOW

def categorize(text):
    t=text.lower()
    if any(w in t for w in ('poland','polish','nato','moldova','moldovan','estonia','border','airspace')):
        return 'nato'
    if any(w in t for w in ('talks','peace','negotiat','summit','diplomac','ceasefire','sanction','agreement')):
        return 'diplomacy'
    return 'military'

def location(text):
    t=text.lower()
    for name, aliases, lat, lon in PLACES:
        if any(a in t for a in aliases):
            return name,lat,lon
    return None

def main():
    prior=json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else {'items': []}
    feeds_received = 0
    found=[]
    for q in QUERIES:
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'en-US','gl':'US','ceid':'US:en'})
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'UkraineMap/1.0 (+https://github.com)'})
            with urllib.request.urlopen(req,timeout=20) as response:
                tree=ET.fromstring(response.read())
        except Exception as ex:
            print('Feed unavailable:',str(ex));continue
        if tree.find('channel') is None:
            continue
        feeds_received += 1
        for el in tree.findall('.//item'):
            title=(el.findtext('title') or '').strip()
            link=(el.findtext('link') or '').strip()
            date=parse_date(el.findtext('pubDate') or '')
            if not title or not link or (NOW-date).total_seconds()>7*86400 or date>NOW+dt.timedelta(hours=2):continue
            loc=location(title)
            if not loc:continue
            place,lat,lon=loc
            source=el.findtext('source') or 'Google News'
            # Feed headlines may be incomplete or unverified; avoid inventing article detail.
            category=categorize(title)
            summary='報道見出しに基づく自動収集記事。事実関係・場所・日時はリンク先の原文で確認してください。'
            found.append({'id':hashlib.sha256((title+link).encode()).hexdigest()[:16], 'title':title,
                'summary':summary,'date':date.date().isoformat(),'source':source,'url':link,
                'place':place,'lat':lat,'lon':lon,'category':category})
    if not feeds_received:
        raise SystemExit('No valid RSS feeds received; existing dataset preserved')
    print(f'Received {feeds_received} RSS feeds')
    # Keep verified initial entries for up to 7 days; do not erase all data on feed failure.
    retained=[x for x in prior.get('items',[]) if x.get('date','') >= (NOW-dt.timedelta(days=7)).date().isoformat()]
    by_id={x['id']:x for x in retained}
    titles={re.sub(r'\W+','',x['title'].lower()) for x in retained}
    for x in found:
        norm=re.sub(r'\W+','',x['title'].lower())
        if norm not in titles:
            by_id[x['id']]=x;titles.add(norm)
    result=sorted(by_id.values(),key=lambda x:x['date'],reverse=True)[:45]
    if not result:
        print('No data; preserving existing dataset');return
    DATA.write_text(json.dumps({'updated_at':NOW.isoformat(timespec='seconds'),'items':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Updated {len(result)} articles ({len(found)} feed candidates)')

if __name__=='__main__':main()
