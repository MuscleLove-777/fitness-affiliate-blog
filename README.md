# フィットネスライフ

フィットネス・筋トレ・ボディメイクの情報ブログ。Hugo + GitHub Pages で運用。

## セットアップ

### 必要なもの

- Hugo Extended v0.159.1 以上
- Git

### ローカル開発

```bash
# リポジトリをクローン（サブモジュール含む）
git clone --recurse-submodules <REPO_URL>

# 開発サーバー起動
hugo server -D

# ビルド
hugo --gc --minify
```

### 記事の追加

```bash
hugo new content posts/記事名.md
```

### デプロイ

`main` ブランチに push すると GitHub Actions で自動的に GitHub Pages にデプロイされます。

### GitHub Pages の設定

1. リポジトリの Settings > Pages へ移動
2. Source を「GitHub Actions」に変更
3. `hugo.toml` の `baseURL` をリポジトリの GitHub Pages URL に更新
