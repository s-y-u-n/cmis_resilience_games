# Buldyrev et al. (2010) シナリオ設計メモ

本ドキュメントは、Buldyrev et al. (2010)  
「Catastrophic cascade of failures in interdependent networks」シナリオの

- 数理モデル
- 実装モジュールとの対応関係
- 代表的な設定（ER / Scale-free / 実ネットワーク）

を整理するためのメモである。

詳細な数理仕様は論文およびノートを参照しつつ、必要に応じて追記していく。

## 1. モデル概要（メモ）

- 2 層（A, B）の相互依存ネットワーク
- 各層は N ノード、同一 ID 空間 {0, …, N-1}
- 依存リンクは 1:1 双方向（A_i ↔ B_i）
- ノード故障は percolation（生残確率 p）と cascading failure によって決定
- 性能指標:
  - giant mutually connected component (MCGC) の相対サイズ `m_infty`
  - 臨界値 p_c

## 2. 実装マッピング（概要）

- ネットワーク構造: `src/cmis_senario_games/core/network_model.py`
- 依存関係: `src/cmis_senario_games/core/interdependency.py`
- 初期故障（percolation）: `src/cmis_senario_games/core/percolation.py`
- カスケードダイナミクス: `src/cmis_senario_games/core/cascade_engine.py`
- 防護型ゲームの特性関数:
  - `src/cmis_senario_games/scenarios/buldyrev2010/value_protection.py`
- ネットワーク生成・読み込み:
  - `src/cmis_senario_games/scenarios/buldyrev2010/network_definition.py`
- 結果可視化:
  - `src/cmis_senario_games/scenarios/buldyrev2010/visualization.py`
- 後処理・集計:
  - `src/cmis_senario_games/scenarios/buldyrev2010/postprocess_metrics.py`

## 3. デフォルト設定（メモ）

代表的な設定は `configs/buldyrev2010/*.yaml` に記述する。

- `er_default.yaml`: ER ネットワーク + 防護型ゲーム
- `sf_default.yaml`: Scale-free ネットワーク + 防護型ゲーム
- `italy_case_study.yaml`: イタリア停電ネットワーク（将来実装予定）

実験定義は `experiments/buldyrev2010/*.yaml` に記述し、
`core/experiment_runner.py` から実行する。

## 4. TODO

- 論文からの数式・パラメータの抜き出し
- MCGC 計算アルゴリズムの pseudo code 化
- 実データ（イタリア停電）の入手元と前処理仕様の整理

