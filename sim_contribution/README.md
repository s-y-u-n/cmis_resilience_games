# sim_contribution

観測ログベースのチーム編成シミュレーション（チームサイズ1–3 / 2次相性 + 調整コスト + スキル補完性）。

## 要件

- Python 3.12
- Poetry

## セットアップ

```bash
poetry install
```

## 実行

```bash
poetry run sim-contribution run --n 12 --T 200 --d 8 --seed 0 --noise-sigma 1.0
```

出力は `outputs/run_<timestamp>/` に生成されます。

## 生成物

- `outputs/.../data/coalitions.csv`: |S|<=3 の全提携と `mu/comp/cost`
- `outputs/.../data/timeseries_<Algo>.csv`: 指標A/B と分布統計（min/median/max/quantiles）
- `outputs/.../data/team_mu_samples_<Algo>.csv`: 全期・全採用チームの `mu(S)` サンプル
- `outputs/.../plots/*.png`: 指標A/B と分布の可視化

