# Ukraine Situation Map

日本語のニュース地図。Leaflet + OpenStreetMap タイル、静的 JSON データ、GitHub Actions による毎日の自動収集で動作します。

## 公開方法

1. GitHub に新規の **public** リポジトリを作り、このフォルダの中身（`.github` を含む）をアップロードします。
2. Settings → Pages → Build and deployment → Source で GitHub Actions を選択します。
3. Actions → Daily Ukraine news update → Run workflow で初回手動更新。以降は毎日 00:20 UTC / 09:20 JST に実行予定です（GitHub の混雑で遅延することがあります）。
4. 公開 URL は `https://<ユーザー名>.github.io/<リポジトリ名>/`。

## ローカルプレビュー

`python -m http.server 8000` をフォルダ内で実行し、`http://localhost:8000/` を開いてください。

## データ運用上の制約

- 初期データは2026-11-20の公開報道を参照した手動要約です。自動更新分は Google News RSS の見出しを取り込み、位置キーワードで概略プロットします。
- ニュース本文の自動要約ではありません。自動収集記事の説明は見出しベースであることを明示し、元記事の確認を促します。
- 地点は代表座標であり、攻撃地点の精密位置ではありません。地名が見出しにない記事は掲載されません。
- Google News のリンクは配信側のリダイレクト URL で、記事原文へ遷移できない場合があります。
- 同じ事件の異なる見出しは重複し得ます。自動収集は誤分類・誤検出があり、編集者による事実確認に代わりません。
- RSS 取得が全件失敗した場合は既存データを維持します。GitHub Actions は無料枠・規約・アカウント状態に依存します。
