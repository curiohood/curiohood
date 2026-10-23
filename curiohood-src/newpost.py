#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CurioHood 内容管线
------------------
写一篇新文章 → 自动生成页面、更新栏目列表、首页最新区、sitemap。

用法：
  python3 newpost.py new                     # 交互式新建（推荐）
  python3 newpost.py new --title "标题" --column stay --tag Wanning
  python3 newpost.py rebuild                 # 全量重建索引（改了 posts.json 后跑）
  python3 newpost.py list                    # 查看现有文章
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / "curiohood-site"
CONTENT = ROOT / "content"
DATA = ROOT / "posts.json"

ART_GRADIENT = {
    "art-1": "linear-gradient(140deg,#F6F48F 0%,#EDEA54 48%,#C9C63C 100%)",
    "art-2": "linear-gradient(140deg,#F1EFE2 0%,#DDDBC8 48%,#B9B7A2 100%)",
    "art-3": "linear-gradient(140deg,#EDEC9E 0%,#DDDA76 48%,#B7B44E 100%)",
    "art-4": "linear-gradient(140deg,#3C3C36 0%,#23231F 48%,#111111 100%)",
}


def fill(tpl: str, **kw) -> str:
    for k, v in kw.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def nav(p: str = "") -> str:
    return f"""<header class="site-head">
  <div class="head-inner">
    <a class="brand" href="{p}index.html">
      <img class="brand-logo" src="{p}assets/img/logo.png" alt="CurioHood" width="108" height="26">
      <span class="brand-sub">Travel Media</span>
    </a>
    <button class="nav-toggle" aria-label="菜单" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav">
      <a href="{p}index.html">首页</a>
      <a href="{p}city-guide.html">城市指南</a>
      <a href="{p}stay.html">酒店</a>
      <a href="{p}lifestyle.html">生活方式</a>
      <a href="{p}about.html">关于</a>
    </nav>
  </div>
</header>"""


def footer(p: str = "") -> str:
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <img class="brand-logo" src="{p}assets/img/logo.png" alt="CurioHood" style="height:30px;width:auto;">
        <p>旅行生活媒体。世界这么大，圈出你的好奇心。</p>
      </div>
      <div class="foot-col">
        <h4>栏目</h4>
        <a href="{p}city-guide.html">城市指南</a>
        <a href="{p}stay.html">酒店观察</a>
        <a href="{p}lifestyle.html">生活方式</a>
      </div>
      <div class="foot-col">
        <h4>关于</h4>
        <a href="{p}about.html">我们是谁</a>
        <a href="{p}about.html#contact">合作与投稿</a>
        <a href="{p}about.html#zine">纸质 ZINE</a>
      </div>
      <div class="foot-col">
        <h4>关注</h4>
        <a href="{p}about.html#contact">小红书</a>
        <a href="{p}about.html#contact">微信公众号</a>
        <a href="{p}about.html#contact">Instagram</a>
      </div>
    </div>
    <div class="foot-bottom">
      <span>© 2026 CurioHood Travel Media. 保留所有权利。</span>
      <span>Stay Curious.</span>
    </div>
  </div>
</footer>"""


def newsletter(title: str, text: str) -> str:
    return f"""      <div class="newsletter reveal">
        <span class="kicker">Newsletter</span>
        <h2 class="display h2">{title}</h2>
        <p>{text}</p>
        <form class="nl-form">
          <input type="email" placeholder="你的邮箱地址" aria-label="邮箱地址">
          <button class="btn" type="submit">订阅</button>
          <span class="nl-note small" style="flex:1 1 100%;margin-top:10px;"></span>
        </form>
      </div>"""


TEMPLATE_ARTICLE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{PAGE_TITLE}}</title>
<meta name="description" content="{{DESC}}">
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="canonical" href="{{URL}}">
<meta property="og:url" content="{{URL}}">
<meta property="og:title" content="{{OG_TITLE}}">
<meta property="og:description" content="{{DESC}}">
<meta property="og:type" content="article">
<script type="application/ld+json">
{{JSONLD}}
</script>
</head>
<body>

{{NAV}}

<main>
  <article>
    <div class="wrap-narrow">
      <div class="article-head">
        <span class="kicker">{{KICKER}}</span>
        <h1 class="display h1 article-title" style="font-size:clamp(32px,4.6vw,54px);">{{HEADLINE}}</h1>
        <p class="lede">{{LEDE}}</p>
        <div class="article-byline" style="margin-top:30px;">
          <span>文 · {{AUTHOR}}</span>
          <span>{{DATE}}</span>
          <span>{{READ}}</span>
        </div>
      </div>
    </div>

    <div class="wrap">
      <div class="article-hero-art" style="{{HERO_STYLE}};"></div>
    </div>

    <div class="wrap-narrow article-body">
{{BODY}}

      <div class="share-row">
        <span>栏目：{{COLUMN_NAME}}</span>
        <span>·</span>
        <a href="../{{COLUMN_FILE}}">更多{{COLUMN_NAME}}内容 →</a>
      </div>
    </div>
  </article>

  <section class="wrap">
    <div class="next-read">
      <div class="section-head">
        <div>
          <span class="kicker">Keep Reading</span>
          <h2 class="display h2">继续读</h2>
        </div>
        <a class="section-link" href="../index.html">返回首页 →</a>
      </div>
      <div class="grid grid-3">
{{RELATED}}
      </div>
    </div>
  </section>
</main>

{{FOOTER}}

<script src="../assets/js/main.js"></script>
</body>
</html>
"""


def pretty_date(d: str) -> str:
    return d.replace("-", ".")


def hero_style(post: dict, prefix: str = "") -> str:
    """有 hero/cover 图就用图，否则退回渐变色块。"""
    hero = post.get("hero") or post.get("cover")
    if hero:
        pos = post.get("hero_pos") or "center 42%"
        return f"background:url('{prefix}{hero}') {pos}/cover no-repeat"
    return "background:" + ART_GRADIENT.get(post["art"], ART_GRADIENT["art-1"])


def card_art(post: dict, prefix: str = "") -> str:
    """封面图优先；没有图才退回渐变色块。"""
    cover = post.get("cover")
    if cover:
        return (f'<div class="card-art has-img">'
                f'<img src="{prefix}{cover}" alt="{post["title"]}" loading="lazy">'
                f'<span class="card-tag">{post["tag"]}</span></div>')
    return f'<div class="card-art {post["art"]}"><span class="card-tag">{post["tag"]}</span></div>'


def card(post: dict, href_prefix: str = "") -> str:
    return f"""<a class="card reveal" href="{href_prefix}articles/{post['slug']}.html">
  {card_art(post, href_prefix)}
  <h3>{post['title']}</h3>
  <p>{post['excerpt']}</p>
  <div class="card-meta">{pretty_date(post['date'])} · {post['read']}</div>
</a>"""


def soon_card(item: dict) -> str:
    return f"""<div class="card card--soon reveal">
  <div class="card-art {item['art']}"><span class="card-tag">{item['tag']}</span></div>
  <h3>{item['title']}</h3>
  <p>{item['excerpt']}</p>
  <div class="card-meta">{item['meta']}</div>
</div>"""


def sorted_posts(data: dict, column: str = None) -> list:
    posts = data["posts"]
    if column:
        posts = [p for p in posts if p["column"] == column]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def build_column_page(data: dict, key: str) -> None:
    col = data["columns"][key]
    cards = [card(p) for p in sorted_posts(data, key)]
    cards += [soon_card(s) for s in data["soon"].get(key, [])]
    body = "\n".join(cards)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{col['name']} · CurioHood</title>
<meta name="description" content="CurioHood {col['name']}：{col['lede'][:50]}">
<link rel="stylesheet" href="assets/css/style.css">
<link rel="canonical" href="{data['site']['base']}/{col['file']}">
<meta property="og:url" content="{data['site']['base']}/{col['file']}">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "{col['name']}",
  "url": "{data['site']['base']}/{col['file']}",
  "isPartOf": {{"@type": "WebSite", "name": "CurioHood", "url": "{data['site']['base']}/"}}
}}
</script>
</head>
<body>

{nav()}

<main>
  <section class="wrap">
    <div class="page-head">
      <span class="kicker">{col['kicker']}</span>
      <h1 class="display h1">{col['title']}</h1>
      <p class="lede">{col['lede']}</p>
    </div>

    <div class="grid grid-2" style="gap:48px 32px;">
{body}
    </div>
  </section>

  <section class="section">
    <div class="wrap">
{newsletter(col['nl_title'], col['nl_text'])}
    </div>
  </section>
</main>

{footer()}

<script src="assets/js/main.js"></script>
</body>
</html>
"""
    (SITE / col["file"]).write_text(html, encoding="utf-8")


def build_home_hero(data: dict) -> None:
    """重建首页头条轮播（最新 3 篇）。"""
    path = SITE / "index.html"
    html = path.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- HERO:START -->).*?(<!-- HERO:END -->)", re.S)
    if not pattern.search(html):
        print("  ! 首页缺少 HERO 标记，跳过轮播更新")
        return

    latest = sorted_posts(data)[:3]
    parts = []
    tones = []
    for i, p in enumerate(latest):
        col = data["columns"][p["column"]]
        tone = p.get("tone") or ("dark" if p["art"] == "art-4" else "light")
        tones.append(tone)
        active = " is-active" if i == 0 else ""
        title = p.get("headline") or p["title"]
        title_style = f' style="color:{p["title_color"]}"' if p.get("title_color") else ""
        if p.get("cover"):
            pos = p.get("carousel_pos") or "center 45%"
            art = f"background:url('{p['cover']}') {pos}/cover no-repeat;"
        else:
            art = f"background:{ART_GRADIENT[p['art']]};"
        parts.append(f"""    <div class="slide{active}" data-tone="{tone}">
      <div class="slide-art" style="{art}"></div>
      <div class="slide-content">
        <span class="slide-kicker">{col['name']} · {p['tag']}</span>
        <h2 class="slide-title"{title_style}>{title}</h2>
        <p class="slide-sub">{p['lede']}</p>
        <p class="slide-cta"><a class="btn" href="articles/{p['slug']}.html">阅读全文</a></p>
      </div>
      <a class="slide-link" href="articles/{p['slug']}.html" aria-label="阅读{title}"></a>
    </div>""")

    first_tone = tones[0] if tones else "light"

    block = (
        "<!-- HERO:START -->\n"
        f'  <section class="hero-carousel" id="top" data-tone="{first_tone}" aria-label="头条">\n'
        + "\n\n".join(parts)
        + "\n\n"
        '    <button class="carousel-arrow prev" aria-label="上一条">&#8592;</button>\n'
        '    <button class="carousel-arrow next" aria-label="下一条">&#8594;</button>\n'
        '    <div class="carousel-dots" role="tablist" aria-label="头条切换">\n'
        + "\n".join(
            f'      <button class="carousel-dot{" is-active" if i == 0 else ""}" aria-label="第 {i+1} 条"></button>'
            for i in range(len(latest))
        )
        + "\n    </div>\n  </section>\n  "
        + "<!-- HERO:END -->"
    )
    path.write_text(pattern.sub(lambda m: block, html), encoding="utf-8")


def build_sitemap(data: dict) -> None:
    base = data["site"]["base"]
    rows = []
    for loc, lm, pri in [
        ("/", date.today().isoformat(), "1.0"),
        ("/city-guide.html", date.today().isoformat(), "0.9"),
        ("/stay.html", date.today().isoformat(), "0.9"),
        ("/lifestyle.html", date.today().isoformat(), "0.9"),
        ("/about.html", date.today().isoformat(), "0.6"),
        ("/zine/mens-wanning-holiday.html", date.today().isoformat(), "0.7"),
    ]:
        rows.append((loc, lm, pri, "weekly" if pri == "1.0" else "monthly"))
    for p in sorted_posts(data):
        rows.append((f"/articles/{p['slug']}.html", p["date"], "0.8", "monthly"))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, pri, freq in rows:
        out += [
            "  <url>",
            f"    <loc>{base}{loc}</loc>",
            f"    <lastmod>{lm}</lastmod>",
            f"    <changefreq>{freq}</changefreq>",
            f"    <priority>{pri}</priority>",
            "  </url>",
        ]
    out.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


def clean_val(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def parse_md(path: Path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        meta = {}
        for line in parts[1].strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = clean_val(v)
        return meta, parts[2].strip() if len(parts) > 2 else ""
    return {}, text


def sync_from_md(data: dict) -> dict:
    """扫描 content/*.md，把新文章自动登记进 posts.json。"""
    if not CONTENT.exists():
        return data
    for md in sorted(CONTENT.glob("*.md")):
        meta, _ = parse_md(md)
        if not meta:
            continue
        slug = meta.get("slug") or md.stem
        record = {
            "slug": slug,
            "title": meta.get("title", slug),
            "headline": meta.get("headline") or meta.get("title", slug),
            "lede": meta.get("lede", ""),
            "column": meta.get("column", "city-guide"),
            "date": meta.get("date", ""),
            "tag": meta.get("tag", "Field Note"),
            "art": meta.get("art", "art-1"),
            "read": meta.get("read", "6 分钟阅读"),
            "excerpt": meta.get("excerpt", ""),
            "existing": False,
        }
        # 图片字段（可选）：cover 用于卡片/首页轮播，hero 用于文章页大图
        for opt in ("cover", "hero", "hero_pos"):
            if meta.get(opt):
                record[opt] = meta[opt]
        hit = next((p for p in data["posts"] if p["slug"] == slug), None)
        if hit:
            hit.update(record)
        else:
            data["posts"].append(record)
            print(f"  + 登记新文章 {slug}")
    return data


def build_article(data: dict, post: dict) -> None:
    md_path = CONTENT / f"{post['slug']}.md"
    if not md_path.exists():
        print(f"  ! 找不到 {md_path}，跳过")
        return
    meta, body_md = parse_md(md_path)
    body_html = markdown.markdown(body_md, extensions=["extra", "sane_lists"])
    body_html = "\n".join("      " + ln if ln.strip() else ln for ln in body_html.splitlines())

    col = data["columns"][post["column"]]
    url = f"{data['site']['base']}/articles/{post['slug']}.html"
    others = [p for p in sorted_posts(data) if p["slug"] != post["slug"]][:3]
    related = "\n".join(card(p, "../") for p in others)

    jld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "datePublished": post["date"],
        "dateModified": post["date"],
        "inLanguage": "zh-CN",
        "author": {"@type": "Organization", "name": data["site"]["author"]},
        "publisher": {"@type": "Organization", "name": "CurioHood", "url": data["site"]["base"] + "/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }, ensure_ascii=False, indent=2)

    html = fill(
        TEMPLATE_ARTICLE,
        PAGE_TITLE=f"{post['title']} · CurioHood",
        DESC=post["excerpt"],
        URL=url,
        OG_TITLE=post["title"],
        JSONLD=jld,
        NAV=nav("../"),
        KICKER=f"{col['name']} · {post['tag']}",
        HEADLINE=post["headline"],
        LEDE=post["lede"],
        AUTHOR=data["site"]["author"],
        DATE=pretty_date(post["date"]),
        READ=post["read"],
        HERO_STYLE=hero_style(post, "../"),
        BODY=body_html,
        COLUMN_NAME=col["name"],
        COLUMN_FILE=col["file"],
        RELATED=related,
        FOOTER=footer("../"),
    )
    art_dir = SITE / "articles"
    if not art_dir.exists():
        art_dir.mkdir()
    (art_dir / f"{post['slug']}.html").write_text(html, encoding="utf-8")
    print(f"  + articles/{post['slug']}.html")


def rebuild() -> None:
    data = load()
    data = sync_from_md(data)
    save(data)
    print("重建索引页...")
    for key in data["columns"]:
        build_column_page(data, key)
        print(f"  + {data['columns'][key]['file']}")
    build_home_hero(data)
    print("  + index.html（头条轮播）")
    for post in data["posts"]:
        if not post.get("existing"):
            build_article(data, post)
    build_sitemap(data)
    print("  + sitemap.xml")
    print("完成。")


def cmd_new(args) -> None:
    data = load()

    def ask(label, key, default=""):
        cur = getattr(args, key, None)
        if cur:
            return cur
        tip = f"（默认 {default}）" if default else ""
        val = input(f"{label}{tip}: ").strip()
        return val or default

    title = ask("文章标题", "title")
    if not title:
        print("标题不能为空")
        sys.exit(1)
    slug = ask("URL 短名（英文，如 shanghai-plane-tree）", "slug", title_to_slug(title))
    column = ask("栏目 [city-guide / stay / lifestyle]", "column", "city-guide")
    while column not in data["columns"]:
        column = input("请重新输入栏目（city-guide / stay / lifestyle）: ").strip()
    tag = ask("卡片标签（如 Bangkok / Suzhou）", "tag", "Field Note")
    art = ask("视觉色块 [art-1 沙金 / art-2 陶粉 / art-3 苔绿 / art-4 暖橙]", "art", "art-1")
    read = ask("阅读时长标注", "read", "6 分钟阅读")
    lede = ask("导语（文章开头那句话）", "lede", title)
    excerpt = ask("卡片摘要（30 字内）", "excerpt", lede[:40])
    d = ask("日期 YYYY-MM-DD", "date", date.today().isoformat())

    if any(p["slug"] == slug for p in data["posts"]):
        print(f"短名 {slug} 已存在，换个名字")
        sys.exit(1)

    md_path = CONTENT / f"{slug}.md"
    if md_path.exists():
        print(f"{md_path} 已存在，换个短名")
        sys.exit(1)

    md_path.write_text(
        f"""---
title: {title}
slug: {slug}
column: {column}
date: {d}
tag: {tag}
art: {art}
read: {read}
lede: {lede}
excerpt: {excerpt}
---

从这里开始写正文。用 Markdown：

## 小标题

普通段落直接写，空一行分段。

> 引用、金句用大于号。

- 列表项一
- 列表项二

写完保存，再跑一次 `python3 newpost.py rebuild`，或者直接用下面的命令一步到位。
""",
        encoding="utf-8",
    )

    data["posts"].append({
        "slug": slug,
        "title": title,
        "headline": ask("页面大标题（默认同标题）", "headline", title),
        "lede": lede,
        "column": column,
        "date": d,
        "tag": tag,
        "art": art,
        "read": read,
        "excerpt": excerpt,
        "existing": False,
    })
    save(data)
    print(f"\n已创建 {md_path}")
    print("正文写好后执行：python3 newpost.py rebuild")


def title_to_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or date.today().isoformat()


def cmd_list() -> None:
    data = load()
    print(f"{'日期':<12}{'栏目':<14}{'标题'}")
    print("-" * 70)
    for p in sorted_posts(data):
        flag = "  " if p.get("existing") else " *"
        print(f"{p['date']:<12}{p['column']:<14}{p['title']}{flag}")
    print("\n* 表示由 Markdown 生成")


def main() -> None:
    ap = argparse.ArgumentParser(description="CurioHood 内容管线")
    sub = ap.add_subparsers(dest="cmd")
    p_new = sub.add_parser("new", help="新建一篇文章")
    for flag in ["title", "slug", "column", "tag", "art", "read", "lede", "excerpt", "date", "headline"]:
        p_new.add_argument(f"--{flag}")
    sub.add_parser("rebuild", help="全量重建")
    sub.add_parser("list", help="列出文章")
    args = ap.parse_args()

    if args.cmd == "new":
        cmd_new(args)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "rebuild":
        rebuild()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
