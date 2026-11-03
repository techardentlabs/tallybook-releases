import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'src', ROOT / 'site'
HEADER = (SRC / '_header.html').read_text()
FOOTER = (SRC / '_footer.html').read_text()
BASE = 'https://tallybook.online'
TODAY = datetime.date.today().isoformat()

POSTS = []
for f in sorted((SRC / 'blog').glob('posts*.json')):
    POSTS += json.loads(f.read_text())
_seen = set()
POSTS = [p for p in POSTS if not (p['slug'] in _seen or _seen.add(p['slug']))]
POSTS = [p for p in POSTS if (SRC / 'blog' / p['slug'] / 'index.html').exists()]
POST_DATE = {f"/blog/{p['slug']}/": p['date'] for p in POSTS}

COMMON_HEAD = '''<meta name="theme-color" content="#2a62ad">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="TallyBook Blog" href="/blog/feed.xml">
<meta name="robots" content="index, follow, max-image-preview:large">'''


def render(text, url):
    text = re.sub(r'@@HEADER:(.*?)@@', lambda m: HEADER.replace('STRIP', m.group(1)), text)
    text = text.replace('@@FOOTER@@', FOOTER)
    extra = COMMON_HEAD
    if 'rel="canonical"' not in text:
        extra += f'\n<link rel="canonical" href="{BASE}{url}">'
    if '<html lang="en">' in text:
        text = text.replace('<html lang="en">', '<html lang="en-IN">', 1)
    return text.replace('</head>', extra + '\n</head>', 1)


def blog_index():
    cards = []
    for p in sorted(POSTS, key=lambda p: (p['date'], p['title']), reverse=True):
        cards.append(
            f'<div class="card"><div class="tag">{html.escape(p["tag"])} · {p["date"]}</div>'
            f'<h3><a href="/blog/{p["slug"]}/">{html.escape(p["title"])}</a></h3>'
            f'<p>{html.escape(p["description"])}</p></div>'
        )
    items = [
        {'@type': 'ListItem', 'position': i + 1, 'url': f'{BASE}/blog/{p["slug"]}/', 'name': p['title']}
        for i, p in enumerate(sorted(POSTS, key=lambda p: p['title']))
    ]
    ld = json.dumps({'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'TallyBook Blog', 'itemListElement': items}, ensure_ascii=False)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>TallyBook Blog: GST, accounting and switching from Tally</title>'
        '<meta name="description" content="Practical guides for Indian businesses: GST billing and returns, inventory, payroll, TDS, bank reconciliation, reports and moving from Tally to TallyBook.">'
        '<meta property="og:type" content="website"><meta property="og:title" content="TallyBook Blog">'
        '<meta property="og:description" content="Practical accounting and GST guides for Indian businesses.">'
        f'<meta property="og:url" content="{BASE}/blog/"><meta property="og:image" content="{BASE}/assets/shots/gateway.png">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<script type="application/ld+json">{ld}</script>'
        '<link rel="stylesheet" href="/assets/style.css"></head><body>'
        '@@HEADER:Blog@@<section><div class="wrap"><h1 style="font-size:34px;margin:0 0 8px">Blog</h1>'
        '<p style="color:var(--muted);margin:0 0 24px">Plain-language guides for business owners, accountants and students.</p>'
        f'<div class="grid post-list">{"".join(cards)}</div></div></section>@@FOOTER@@</body></html>'
    )


def rss():
    items = ''.join(
        f'<item><title>{html.escape(p["title"])}</title><link>{BASE}/blog/{p["slug"]}/</link>'
        f'<guid isPermaLink="true">{BASE}/blog/{p["slug"]}/</guid>'
        f'<pubDate>{datetime.datetime.fromisoformat(p["date"]).strftime("%a, %d %b %Y 09:00:00 +0530")}</pubDate>'
        f'<description>{html.escape(p["description"])}</description></item>'
        for p in sorted(POSTS, key=lambda p: p['date'], reverse=True)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>TallyBook Blog</title>'
        f'<link>{BASE}/blog/</link><description>Accounting and GST guides for Indian businesses</description>'
        f'<language>en-IN</language>{items}</channel></rss>\n'
    )


def sitemap(pages):
    out = []
    for url, images in pages:
        lastmod = POST_DATE.get(url, TODAY)
        prio = '1.0' if url == '/' else '0.9' if url == '/download/' else '0.8' if url.startswith('/blog/') else '0.5'
        imgs = ''.join(f'<image:image><image:loc>{BASE}{i}</image:loc></image:image>' for i in sorted(set(images)))
        out.append(f'<url><loc>{BASE}{url}</loc><lastmod>{lastmod}</lastmod><priority>{prio}</priority>{imgs}</url>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + '\n'.join(out)
        + '\n</urlset>\n'
    )


pages = []
for src in sorted(SRC.rglob('*.html')):
    rel = src.relative_to(SRC)
    if rel.name.startswith('_'):
        continue
    url = '/' + str(rel).replace('index.html', '')
    text = render(src.read_text(), url)
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    if rel.name == '404.html':
        continue
    pages.append((url, re.findall(r'src="(/assets/shots/[^"]+\.png)"', text)))

(OUT / 'blog').mkdir(exist_ok=True)
(OUT / 'blog' / 'index.html').write_text(render(blog_index(), '/blog/'))
(OUT / 'blog' / 'feed.xml').write_text(rss())
pages.append(('/blog/', []))

for os_dir in ['windows', 'mac', 'linux']:
    p = OUT / 'download' / os_dir / 'index.html'
    t = p.read_text()
    if 'noindex' not in t:
        p.write_text(t.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta name="robots" content="noindex, follow">', 1))

(OUT / 'sitemap.xml').write_text(sitemap(sorted(pages)))
(OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /download/windows/\nDisallow: /download/mac/\nDisallow: /download/linux/\n\nSitemap: {BASE}/sitemap.xml\n')
(OUT / 'site.webmanifest').write_text(json.dumps({
    'name': 'TallyBook', 'short_name': 'TallyBook', 'start_url': '/', 'display': 'browser',
    'background_color': '#ffffff', 'theme_color': '#2a62ad',
    'icons': [{'src': '/assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}],
}, indent=2) + '\n')
(OUT / '.well-known').mkdir(exist_ok=True)
expires = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
(OUT / '.well-known' / 'security.txt').write_text(f'Contact: https://github.com/techardentlabs/tallybook/security/advisories/new\nExpires: {expires}T00:00:00.000Z\nPreferred-Languages: en\nCanonical: {BASE}/.well-known/security.txt\n')
(OUT / '.nojekyll').write_text('')
print('built', len(pages), 'pages,', len(POSTS), 'posts')
