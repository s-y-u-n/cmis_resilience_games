# <paper_key> → 貢献度評価フレームワーク写像

このファイルでは、対象論文のモデルを
本リポジトリの「プレイヤー → v(S) → Shapley」フレームワークに
どのように落とし込んでいるかを整理する。

## 1. ゲームタイプの選択

- GameType:
  - Protection / DamageReduction / CreditAllocation のどれとして解釈するか
  - 理由（論文の文脈との対応）:

## 2. プレイヤー定義

- プレイヤー = ?
  - ノード、ノードペア、エッジ、他
- 本実装での選択:
  - プレイヤー ID i が何を意味するか
  - `coalition[i] = True` をどう解釈するか

## 3. 特性関数 v(S) の定義

- 性能指標:
  - 何を価値として評価するか（MCGC、サービスレベル、被害コストなど）
- 確率構造:
  - 初期故障 / シナリオ生成のモデル
  - v(S) = E[F_S(ω)] の形で期待値を取るかどうか
- 実装クラス:
  - どのシナリオ固有 ValueFunction に対応させるか

## 4. モデル構成要素と core モジュールの対応

- ネットワーク構造:
  - `MultiLayerNetwork`, `NetworkLayer` との対応
- 依存関係:
  - `DependencyMapping` との対応
- 初期故障:
  - `PercolationParams`, `sample_initial_failure` など
- カスケード:
  - `run_cascade` もしくはシナリオ固有のカスケードロジック
- v(S):
  - シナリオ固有 ValueFunction のメソッド

## 5. YAML 設定との対応

- `configs/<paper_key>/*.yaml`:
  - network / percolation / value_function / shapley の構造
- `experiments/<paper_key>/*.yaml`:
  - scenario_config / output_dir / figure_dir / mode など

