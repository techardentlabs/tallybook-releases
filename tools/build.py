import json, re, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'src', ROOT / 'site'
HEADER = (SRC / '_header.html').read_text()
FOOTER = (SRC / '_footer.html').read_text()
POSTS = json.loads((SRC / 'blog' / 'posts.json').read_text())
BASE = 'https://tallybook.online'


def render(text):
    text = re.sub(r'@@HEADER:(.*?)@@', lambda m: HEADER.replace('STRIP', m.group(1)), text)
    return text.replace('@@FOOTER@@', FOOTER)


def blog_index():
    cards = []
    for p in sorted(POSTS, key=lambda p: p['date'], reverse=True):
        cards.append(
            f'<div class="card"><div class="tag">{html.escape(p["tag"])} · {p["date"]}</div>'
            f'<h3><a href="/blog/{p["slug"]}/">{html.escape(p["title"])}</a></h3>'
            f'<p>{html.escape(p["description"])}</p></div>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>TallyBook Blog: GST, accounting and switching from Tally</title>'
        '<meta name="description" content="Practical guides for Indian businesses: GST billing, returns, inventory, payroll, TDS, bank reconciliation and moving from Tally to TallyBook.">'
        '<link rel="icon" href="/assets/icon.png"><link rel="stylesheet" href="/assets/style.css"></head><body>'
        '@@HEADER:Blog@@<section><div class="wrap"><h1 style="font-size:34px;margin:0 0 8px">Blog</h1>'
        '<p style="color:var(--muted);margin:0 0 24px">Plain-language guides for business owners, accountants and students.</p>'
        f'<div class="grid post-list">{"".join(cards)}</div></div></section>@@FOOTER@@</body></html>'
    )


def sitemap(pages):
    urls = ''.join(f'<url><loc>{BASE}{p}</loc></url>' for p in pages)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'


pages = []
for src in sorted(SRC.rglob('*.html')):
    rel = src.relative_to(SRC)
    if rel.name.startswith('_'):
        continue
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(src.read_text()))
    pages.append('/' + str(rel).replace('index.html', ''))
(OUT / 'blog').mkdir(exist_ok=True)
(OUT / 'blog' / 'index.html').write_text(render(blog_index()))
pages.append('/blog/')
pages += ['/download/windows/', '/download/mac/', '/download/linux/']
(OUT / 'sitemap.xml').write_text(sitemap(sorted(set(pages))))
(OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
print('built', len(pages), 'pages')
