"""
商品データからHugo用のMarkdown記事を自動生成するモジュール
テンプレートのバリエーションを用意し、重複コンテンツを回避する
"""

import os
import re
import random
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from config import Config


# ============================================================
# 記事テンプレート群（バリエーションで重複コンテンツを回避）
# ============================================================

RESPONSIVE_CSS = """
<style>
.sample-gallery {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 1em 0;
}
.sample-gallery img {
  width: 100%;
  border-radius: 4px;
  cursor: pointer;
}
.cta-box a {
  display: inline-block;
  padding: 15px 40px;
  background: #e63946;
  color: #fff !important;
  text-decoration: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: bold;
}
.sns-links {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin: 1.5em 0;
}
.video-container {
  position: relative;
  width: 100%;
  max-width: 560px;
  margin: 1.5em auto;
}
.video-container iframe {
  width: 100%;
  height: auto;
  aspect-ratio: 560/360;
  border-radius: 8px;
}
@media (max-width: 768px) {
  .sample-gallery {
    grid-template-columns: repeat(2, 1fr);
  }
  .cta-box a {
    display: block;
    width: 100%;
    text-align: center;
    padding: 15px 20px;
  }
  .sns-links {
    flex-direction: column;
  }
  .sns-links a {
    text-align: center;
  }
}
</style>
"""

ARTICLE_TEMPLATES = [
    # テンプレートA: ストレート紹介型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["フィットネス", "おすすめ"]
draft: false
description: "{{ meta_description }}"
---

{{ responsive_css }}

## {{ hook_title }}

{{ intro_text }}

<!--more-->

![{{ title }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### 商品情報

| 項目 | 内容 |
|------|------|
{% if price %}| 価格 | {{ price }} |
{% endif %}{% if maker %}| メーカー | {{ maker }} |
{% endif %}{% if series %}| シリーズ | {{ series }} |
{% endif %}{% if actresses %}| 出演 | {{ actresses }} |
{% endif %}

{{ body_text }}

{{ cta_section }}

---

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートB: レビュー風型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["レビュー", "フィットネス"]
draft: false
description: "{{ meta_description }}"
---

{{ responsive_css }}

{{ intro_text }}

<!--more-->

## 作品の見どころ

![{{ title }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

{{ body_text }}

{% if actresses %}
### 出演者について

{{ actresses }}さんが出演するこの作品。ファンなら見逃せない一本です。
{% endif %}

{% if maker %}
> **{{ maker }}**からリリースされたこの作品は、クオリティの高さで定評があります。
{% endif %}

{{ cta_section }}

---

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートC: ランキング・おすすめ型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["ピックアップ", "注目作品"]
draft: false
description: "{{ meta_description }}"
---

{{ responsive_css }}

## 本日のピックアップ

{{ intro_text }}

<!--more-->

![{{ title }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### この作品をおすすめする理由

{{ body_text }}

{% if price %}
**価格: {{ price }}** --- コスパも申し分なし！
{% endif %}

{{ cta_section }}

---

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートD: Q&A型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["フィットネス", "Q&A"]
draft: false
description: "{{ meta_description }}"
---

{{ responsive_css }}

{{ intro_text }}

<!--more-->

![{{ title }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### Q. どんな作品？

{{ body_text }}

### Q. 価格は？

{% if price %}{{ price }}で視聴できます。{% else %}詳細はリンク先でご確認ください。{% endif %}

{% if actresses %}
### Q. 誰が出演している？

{{ actresses }}さんが出演しています。
{% endif %}

{{ cta_section }}

---

{{ sns_section }}

{{ related_section }}
"""),
]


# ============================================================
# 導入文のバリエーション
# ============================================================

INTRO_VARIATIONS = [
    "今回は**「{title}」**をご紹介します。{genre_text}が好きな方にはたまらない作品です。",
    "注目の作品が登場しました！**「{title}」**は、{genre_text}好きなら要チェックの一本。",
    "{genre_text}を探している方に朗報です。**「{title}」**が今おすすめ！",
    "話題の**「{title}」**をピックアップ。{genre_text}をテーマにした注目作品です。",
    "**「{title}」**が気になる方へ。{genre_text}ジャンルの中でも特に評価の高い一作をご紹介。",
    "本日のおすすめは**「{title}」**です。{genre_text}ファンの間で話題になっています。",
    "新着作品の中から**「{title}」**をセレクト。{genre_text}が充実した内容です。",
]

BODY_VARIATIONS = [
    "この作品の魅力は、何といってもクオリティの高さです。映像美・演出ともにハイレベルで、最後まで飽きさせない構成になっています。",
    "ストーリー展開がしっかりしていて、見応えがあります。細部までこだわった演出が光る一作です。",
    "評価の高い作品だけあって、内容の充実度はさすがの一言。じっくり楽しみたい方におすすめです。",
    "全体的に完成度が高く、リピートしたくなるクオリティ。ファンの期待を裏切らない仕上がりです。",
    "注目ポイントが多く、見るたびに新しい発見がある作品。コレクションに加えたい一本です。",
    "しっかりとした作り込みが感じられる作品です。初めての方もリピーターも満足できるクオリティ。",
]

HOOK_TITLES = [
    "注目の作品をご紹介",
    "今チェックすべき一本",
    "見逃し厳禁！話題の作品",
    "本日のイチオシ",
    "ファン必見のピックアップ",
    "今すぐチェックしたい作品",
]


def generate_articles(
    products: list[dict],
    output_dir: str = "",
) -> list[str]:
    """
    商品データからHugo用Markdown記事を生成する

    Args:
        products: fetch_productsで取得した商品データリスト
        output_dir: 出力先ディレクトリ（空の場合はConfig.CONTENT_DIR）

    Returns:
        生成されたファイルパスのリスト
    """
    if not output_dir:
        output_dir = Config.CONTENT_DIR

    # 出力ディレクトリを作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generated_files = []

    for i, product in enumerate(products):
        try:
            filepath = _generate_single_article(product, output_dir, i)
            if filepath:
                generated_files.append(filepath)
                print(f"[生成] {Path(filepath).name}")
        except Exception as e:
            print(f"[エラー] 記事生成に失敗: {product.get('title', '不明')} - {e}")

    print(f"\n[完了] {len(generated_files)}件の記事を生成しました → {output_dir}")
    return generated_files


def _generate_single_article(
    product: dict,
    output_dir: str,
    index: int,
) -> str:
    """
    1商品分の記事を生成する

    Args:
        product: 商品データ辞書
        output_dir: 出力先ディレクトリ
        index: 商品のインデックス（ファイル名衝突回避用）

    Returns:
        生成されたファイルパス
    """
    title = product.get("title", "タイトル不明")
    image_url = product.get("image_url", "")
    affiliate_url = product.get("affiliate_url", "")
    price = product.get("price", "")
    genres = product.get("genres", [])
    actresses = ", ".join(product.get("actresses", []))
    maker = product.get("maker", "")
    series = product.get("series", "")
    sample_images = product.get("sample_images", [])
    sample_movie_url = product.get("sample_movie_url", "")

    # 日付の整形（APIの日付 or 今日の日付）
    raw_date = product.get("date", "")
    article_date = _format_date(raw_date)

    # スラッグの生成
    slug = _make_slug(product.get("content_id", ""), index)

    # ファイル名
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    # 既存ファイルがあればスキップ
    if os.path.exists(filepath):
        print(f"[スキップ] 既に存在: {filename}")
        return ""

    # タグの生成
    tag_list = genres[:5] if genres else ["フィットネス", "おすすめ"]
    tags = ", ".join(f'"{t}"' for t in tag_list)

    # ジャンルテキスト（導入文用）
    genre_text = "・".join(genres[:3]) if genres else "フィットネス"

    # テンプレート変数の準備
    intro_text = random.choice(INTRO_VARIATIONS).format(
        title=_truncate(title, 40),
        genre_text=genre_text,
    )
    body_text = random.choice(BODY_VARIATIONS)
    hook_title = random.choice(HOOK_TITLES)
    meta_description = _truncate(f"{title} - {genre_text}ジャンルのおすすめ作品を紹介", 120)

    # CTAセクションの生成
    cta_section = _build_cta(affiliate_url, title)

    # サンプル画像ギャラリー
    sample_gallery = _build_sample_gallery(sample_images)

    # サンプル動画セクション
    sample_movie = _build_sample_movie(sample_movie_url)

    # SNSリンクセクション
    sns_section = _build_sns_section()

    # 関連商品セクション
    related_section = _build_related_section()

    # ランダムにテンプレートを選択
    template = random.choice(ARTICLE_TEMPLATES)

    # レンダリング
    content = template.render(
        title=_truncate(title, 60),
        date=article_date,
        tags=tags,
        meta_description=meta_description,
        hook_title=hook_title,
        intro_text=intro_text,
        image_url=image_url,
        body_text=body_text,
        price=price,
        maker=maker,
        series=series,
        actresses=actresses,
        cta_section=cta_section,
        sample_gallery=sample_gallery,
        sample_movie=sample_movie,
        sns_section=sns_section,
        related_section=related_section,
        responsive_css=RESPONSIVE_CSS,
    )

    # ファイル書き出し
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

    return filepath


def _format_date(raw_date: str) -> str:
    """常に生成時の今日の日付をHugo用のISO形式で返す（未来日付を防止）"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _make_slug(content_id: str, index: int) -> str:
    """URLスラッグを生成する"""
    if content_id:
        # 英数字とハイフンのみ残す
        slug = re.sub(r"[^a-zA-Z0-9]", "-", content_id).strip("-").lower()
        if slug:
            return slug
    return f"product-{index:03d}"


def _truncate(text: str, max_len: int) -> str:
    """テキストを指定文字数で切り詰める"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _build_cta(affiliate_url: str, title: str) -> str:
    """CTAボタンセクションを生成する"""
    if not affiliate_url:
        return ""

    cta_texts = [
        "詳細をチェックする",
        "今すぐ見る",
        "この作品をチェック",
        "詳しくはこちら",
        "作品ページへ",
    ]
    cta_text = random.choice(cta_texts)

    return f"""
<div class="cta-box" style="text-align: center; margin: 2em 0;">
  <a href="{affiliate_url}" rel="nofollow" target="_blank">
    {cta_text}
  </a>
  <p style="margin-top: 0.5em; font-size: 0.85em; color: #888;">※外部サイトに移動します</p>
</div>
"""


def _build_sample_gallery(sample_images: list[str]) -> str:
    """サンプル画像ギャラリーを生成する（最大6枚、レスポンシブグリッド）"""
    if not sample_images:
        return ""

    images = sample_images[:6]

    gallery_html = """
### サンプル画像

<div class="sample-gallery">
"""
    for img_url in images:
        gallery_html += f'  <img src="{img_url}" alt="サンプル画像" loading="lazy" />\n'

    gallery_html += "</div>\n"
    return gallery_html


def _build_sample_movie(sample_movie_url: str) -> str:
    """サンプル動画の埋め込みセクションを生成する"""
    if not sample_movie_url:
        return ""

    return f"""
### サンプル動画を見る

<div class="video-container">
  <iframe src="{sample_movie_url}" frameborder="0" allowfullscreen></iframe>
</div>
"""


def _build_sns_section() -> str:
    """SNSリンクセクションを生成する"""
    return """
### フォロー & もっと見る

<div class="sns-links">
  <a href="https://www.patreon.com/c/MuscleLove" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #FF424D; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    もっとフィットネスコンテンツを見る
  </a>
  <a href="https://x.com/MuscleGirlLove7" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    フォローして最新情報をGET
  </a>
</div>
"""


def _build_related_section() -> str:
    """関連コンテンツセクションを生成する"""
    suggestions = [
        "他にもフィットネス関連の作品を多数紹介しています。",
        "このジャンルの他のおすすめ作品もチェックしてみてください。",
        "関連するおすすめ作品は、カテゴリーページからご覧いただけます。",
    ]
    return f"""
### あわせてチェック

{random.choice(suggestions)}

[カテゴリー一覧を見る](/categories/) | [タグ一覧を見る](/tags/)
"""


if __name__ == "__main__":
    # テスト用のダミーデータで動作確認
    test_products = [
        {
            "title": "テスト商品 筋肉フィットネス",
            "image_url": "https://example.com/image.jpg",
            "affiliate_url": "https://example.com/affiliate",
            "price": "1,980円",
            "date": "2026-03-28 10:00:00",
            "content_id": "test001",
            "product_id": "test001",
            "genres": ["フィットネス", "トレーニング"],
            "actresses": ["テスト出演者"],
            "maker": "テストメーカー",
            "series": "",
            "sample_images": [
                "https://example.com/sample1.jpg",
                "https://example.com/sample2.jpg",
                "https://example.com/sample3.jpg",
            ],
            "sample_movie_url": "https://example.com/sample_movie.mp4",
        }
    ]
    files = generate_articles(test_products)
    for f in files:
        print(f"  生成: {f}")
