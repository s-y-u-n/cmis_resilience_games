# docs/papers/ ディレクトリについて

このディレクトリは、「元論文ごと」に

- 論文の概要
- 実世界の問題モデル
- 本リポジトリの貢献度評価フレームワークへの写像

を整理して保存するための場所。

## 構造のルール

1 つの論文につき、以下のようなサブディレクトリを 1 つ作ることを想定する：

- `docs/papers/<paper_key>/`
  - `<paper_key>` は `buldyrev2010` のような短い識別子（著者名＋年など）。
  - 各論文ディレクトリの中身は、基本的に共通の構造をとる：
    - `original/`  
      元論文 PDF 等を置く場所（Git に含めるかどうかは任意）。
    - `index.md`  
      その論文パッケージの入口・リンク集。
    - `01_paper_overview.md`  
      論文の書誌情報、Abstract 要約、数理モデル・結果の整理。
    - `02_real_world_model.md`  
      実世界の問題設定（インフラ・ネットワーク・データ構造）の整理。
    - `03_framework_mapping.md`  
      論文モデルを「プレイヤー → v(S) → Shapley」フレームワークにどう写像しているか。
    - `99_notes_todo.md`  
      メモ・TODO 用の自由なノート。

`docs/papers/buldyrev2010/` が、この構造の具体例になっている。

## 新しい論文用ディレクトリの作り方

新しい論文（例: `somepaper2022`）に対して同様のゲーム構築を行う場合は、
まず次のようなディレクトリを作る：

```bash
mkdir -p docs/papers/somepaper2022/original
cp docs/papers/_template/* docs/papers/somepaper2022/
```

その上で、

- `original/` に元論文 PDF を置く
- `01_paper_overview.md` に論文概要を書く
- `02_real_world_model.md` に実世界モデルを整理する
- `03_framework_mapping.md` にフレームワークへの写像を整理する

という流れで、Buldyrev2010 と同様のゲーム構築ドキュメントを作成する。

