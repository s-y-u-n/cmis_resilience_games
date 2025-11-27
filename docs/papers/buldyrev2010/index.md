# Buldyrev et al. (2010) 論文パッケージ

このディレクトリは、Buldyrev et al. (2010)
“Catastrophic cascade of failures in interdependent networks”
に関する資料をまとめる場所。

- 元論文そのもの（PDF など）は `original/` 以下に配置することを想定。
- モデルの概要・実世界の問題設定・本リポジトリのフレームワークへの写像は、
  階層化された Markdown で整理する。

関連ファイル・ディレクトリ:

- `original/`  
  → 元論文 PDF 等を配置するディレクトリ（Git には含めない想定）。
- `01_paper_overview.md`  
  → 書誌情報、Abstract 要約、主要な数理モデル・結果の整理。
- `02_real_world_model.md`  
  → 実世界の問題モデル（どのインフラ／データを想定しているか）の整理。
- `03_framework_mapping.md`  
  → 本リポジトリの貢献度評価フレームワークへの写像。
- `99_notes_todo.md`  
  → メモ・未整理のアイデア・TODOなど。

実装側の設計メモは `docs/scenario_buldyrev2010.md` にまとめてあり、
本ディレクトリはあくまで「論文そのものと、その解釈」を中心に置く。

