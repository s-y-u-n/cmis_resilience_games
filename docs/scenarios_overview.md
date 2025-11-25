# シナリオ一覧と対応表

本ドキュメントでは、`cmis_senario_games` リポジトリに実装される
シナリオ（論文パターン）を一覧化し、対応するモジュールを整理する。

## 1. フレームワーク別分類

- Protection（防護型）
- Damage Reduction（被害削減型）
- Credit Allocation（クレジット配分）

現時点では、Protection フレームワークの第 1 例として
Buldyrev et al. (2010) を実装対象とする。

## 2. シナリオ一覧（暫定）

### Buldyrev et al. (2010) – Protection

- フレームワーク: `GameType.PROTECTION`
- シナリオモジュール:
  - `src/cmis_senario_games/scenarios/buldyrev2010/`
- 代表的な config:
  - `configs/buldyrev2010/er_default.yaml`
  - `configs/buldyrev2010/sf_default.yaml`
  - `configs/buldyrev2010/italy_case_study.yaml`
- 代表的な実験定義:
  - `experiments/buldyrev2010/er_pc_sweep.yaml`
  - `experiments/buldyrev2010/node_importance_shapley.yaml`

## 3. 将来拡張のメモ

- Damage Reduction 系論文
- Credit Allocation 系論文
- 実データ利用シナリオ（地域別インフラネットワーク等）

これらは `src/cmis_senario_games/scenarios/<paper_short_name>/` として追加し、
共通の core エンジン (`src/cmis_senario_games/core/`) を再利用する。

