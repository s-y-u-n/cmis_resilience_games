cmis_senario_games
==================

Resilience cooperation game engine for virtual lifeline / interdependent networks.

現在の基本設計は Buldyrev et al. (2010) の相互依存ネットワーク・パーコレーションモデルを
「防護型ゲーム（Protection Game）」として実装するパターンを軸に構成している。

詳しい設計方針・モジュール構成は次を参照:

- `docs/design_cmis_senario_games.md`
- `docs/scenario_buldyrev2010.md`
- `docs/scenarios_overview.md`

## インストールと開発

```bash
poetry install
```

## 実験ランナー（雛形）

Buldyrev2010 パターンに基づく実験は、将来的に次のような形で実行する想定:

```bash
python -m cmis_senario_games.run_experiment \
  --config experiments/buldyrev2010/node_importance_shapley.yaml
```

現時点では `core/experiment_runner.py` および `run_experiment` モジュールは
プレースホルダ実装であり、今後の実装で有効化する。

