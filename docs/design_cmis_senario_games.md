# cmis_senario_games 基本設計書（Buldyrev et al. パターン）

本ドキュメントは、GitHub リポジトリ `cmis_senario_games` の基本設計を示す。  
第1弾として、Buldyrev et al. (2010) の相互依存ネットワーク・パーコレーションモデルを  
「防護型ゲーム（Protection Game）」として実装するパターンを中心に記述する。

将来的には、

- 防護型（Protection）
- 被害削減量（Damage Reduction）
- クレジット配分（Credit Allocation）

の 3 フレームワーク × 約 3 本の論文パターンを並列で管理・実装する構成を想定する。

---

## 1. リポジトリ全体構成

標準的なシミュレーションシステムの構成ルールに従い、  
「コアエンジン」「シナリオ（論文）依存コード」「実験定義」「出力」「ドキュメント」を分離する。

```text
cmis_senario_games/
  README.md
  pyproject.toml / setup.cfg          # Python パッケージ定義
  .gitignore
  docs/
    design_cmis_senario_games.md      # 本ドキュメント
    scenario_buldyrev2010.md          # Buldyrev 特化の理論・仕様
    scenarios_overview.md             # 全シナリオ一覧と対応表
  src/
    cmis_senario_games/
      __init__.py
      core/                           # 共通エンジン層
        __init__.py
        network_model.py
        interdependency.py
        percolation.py
        cascade_engine.py
        value_functions.py
        contribution_shapley.py
        contribution_lexcel.py
        experiment_runner.py
        io_config.py
        io_results.py
      scenarios/                      # 論文・フレームワーク別シナリオ
        __init__.py
        buldyrev2010/
          __init__.py
          config_schema.py
          network_definition.py
          value_protection.py
          visualization.py
          postprocess_metrics.py
        # future:
        #  xxx20yy_damage_reduction/
        #  zzz20ww_credit_allocation/
  configs/
    buldyrev2010/
      er_default.yaml                 # ER ネットワークの防護型ゲーム設定
      sf_default.yaml                 # Scale-free ネットワーク設定
      italy_case_study.yaml           # イタリア停電ケース模倣
  experiments/
    buldyrev2010/
      er_pc_sweep.yaml                # p と pc 周辺の sweep 定義
      node_importance_shapley.yaml    # Shapley によるノード重要度評価
  data/
    raw/
      # 実データ（例：イタリア停電ネットワーク）を置く場所
    processed/
      # 前処理済ネットワーク・依存リンク
  outputs/
    logs/
    results/
      buldyrev2010/
        er_pc_sweep/
        node_importance_shapley/
    figures/
      buldyrev2010/
        pc_curves.png
        node_importance_heatmap.png
  notebooks/
    buldyrev2010_exploration.ipynb    # 試行・可視化用
  tests/
    test_core_*.py
    test_scenario_buldyrev2010_*.py
```

---

## 2. ドメインモデル設計

### 2.1 コアの抽象モデル

`src/cmis_senario_games/core/network_model.py`

```python
@dataclass
class NetworkLayer:
    name: str                     # "A" (power), "B" (communication) 等
    num_nodes: int
    edges: np.ndarray             # shape: (m, 2) の隣接リスト
    degree_distribution: Optional[np.ndarray] = None


@dataclass
class MultiLayerNetwork:
    layers: Dict[str, NetworkLayer]       # {"A": NetworkLayer, "B": NetworkLayer}
    # ノード ID は 0..N-1 を共有し、依存関係で層を跨いで紐づく
```

`src/cmis_senario_games/core/interdependency.py`

```python
@dataclass
class DependencyMapping:
    # Buldyrev2010 では 1:1 双方向依存
    # dep_A_to_B[i] = j  (A 層の i が B 層の j に依存)
    dep_A_to_B: np.ndarray
    dep_B_to_A: np.ndarray        # 通常は dep_A_to_B の逆写像


@dataclass
class InterdependentSystem:
    network: MultiLayerNetwork
    dependency: DependencyMapping
```

Buldyrev2010 シナリオは、`InterdependentSystem` の特殊ケースとして

- 層数 = 2
- 依存リンク = 1:1 双方向

を仮定する。

### 2.2 シナリオごとのゲームタイプ

「3フレームワーク」を共通インターフェースで扱うため、`GameType` を定義する。

```python
from enum import Enum


class GameType(Enum):
    PROTECTION = "protection"          # 防護型
    DAMAGE_REDUCTION = "damage_reduction"
    CREDIT_ALLOCATION = "credit_allocation"
```

Buldyrev2010 の基本パターンは `GameType.PROTECTION` に該当する。

---

## 3. パーコレーション + カスケードエンジン

`src/cmis_senario_games/core/percolation.py`

- ノード単位での生残確率 (p) に基づき、初期故障状態を生成。
- ゲームごとに「防護集合 (S)」などを考慮した修正状態を生成。

```python
@dataclass
class PercolationParams:
    survival_prob: float           # p
    random_seed: Optional[int] = None


def sample_initial_failure(system: InterdependentSystem,
                           params: PercolationParams) -> np.ndarray:
    """
    戻り値: alive_mask (shape: (N,), bool)
    """
    ...
```

`src/cmis_senario_games/core/cascade_engine.py`

- Buldyrev のアルゴリズムに従い、互いに依存する 2 層ネットワーク上での cascading failure を実装。
- 入力:
  - `InterdependentSystem`
  - 初期 `alive_mask`（ゲームごとの防護集合適用後）
- 出力:
  - 最終 `alive_mask`
  - 各ステージの giant mutually connected component (MCGC) サイズなど

```python
@dataclass
class CascadeResult:
    final_alive_mask: np.ndarray     # shape: (N,)
    m_infty: float                   # MCGC 相対サイズ
    history: Dict[str, Any]          # ステップごとのメトリクス


def run_cascade(system: InterdependentSystem,
                initial_alive_mask: np.ndarray) -> CascadeResult:
    ...
```

---

## 4. 特性関数 (v(S)) の共通定義

`src/cmis_senario_games/core/value_functions.py`

### 4.1 抽象インターフェース

```python
class ValueFunction(Protocol):
    game_type: GameType

    def evaluate(self, coalition: np.ndarray) -> float:
        """
        coalition: shape (N,), bool マスク
        返り値: v(S) の値
        """
        ...
```

### 4.2 Buldyrev2010 防護型ゲームの特性関数

Buldyrev2010 / Protection:

- coalition (S) = 防護対象ノード集合
- 特性関数:

\\[
v(S) = \\mathbb{E}_\\omega[ F_S(\\omega) ]
\\]

`F_S(ω)` = MCGC の相対サイズ（cascading failure 後）。

`src/cmis_senario_games/scenarios/buldyrev2010/value_protection.py`

```python
@dataclass
class BuldyrevProtectionConfig:
    percolation: PercolationParams
    num_scenarios: int
    performance_metric: str = "mcgc_size"  # デフォルト MCGC 相対サイズ


class BuldyrevProtectionValue(ValueFunction):
    game_type = GameType.PROTECTION

    def __init__(self,
                 system: InterdependentSystem,
                 config: BuldyrevProtectionConfig):
        self.system = system
        self.config = config

    def evaluate(self, coalition: np.ndarray) -> float:
        """
        coalition[i] = True のノードは「常に生き残る」と解釈。
        Monte Carlo により v(S) を近似。
        """
        total = 0.0
        for _ in range(self.config.num_scenarios):
            alive0 = sample_initial_failure(self.system, self.config.percolation)
            alive0[coalition] = True  # 防護
            result = run_cascade(self.system, alive0)
            total += result.m_infty
        return total / self.config.num_scenarios
```

---

## 5. 貢献度評価（Shapley / lex-cel）

### 5.1 Shapley 値

`src/cmis_senario_games/core/contribution_shapley.py`

- 汎用的に「任意の `ValueFunction` に対して Shapley を近似」。

```python
@dataclass
class ShapleyConfig:
    num_samples: int
    random_seed: Optional[int] = None


def estimate_shapley(value_fn: ValueFunction,
                     num_players: int,
                     config: ShapleyConfig) -> np.ndarray:
    """
    Monte Carlo permutation sampling による Shapley 近似。
    戻り値: shape (num_players,)
    """
    ...
```

Buldyrev2010 シナリオで利用する場合：

- プレイヤー = 各ノード（あるいはノードペア (A_i, B_i)）
- `ValueFunction` = `BuldyrevProtectionValue`
- Shapley 値 = 「防護投資における限界レジリエンス貢献度」

### 5.2 lex-cel 型ランク付け

`src/cmis_senario_games/core/contribution_lexcel.py`

- 事前に計算された貢献度ベクトル（Shapley, Banzhaf など）から、特定の lexicographic + cell-based ルールで順位付けを行う。

```python
@dataclass
class LexCelConfig:
    # 例：一次指標 Shapley、二次指標 何らかの距離中心性など
    primary_weight: float = 1.0


def rank_players_lexcel(contributions: np.ndarray,
                        tie_break_metric: Optional[np.ndarray],
                        config: LexCelConfig) -> np.ndarray:
    """
    戻り値: 順位（0=最上位）
    """
    ...
```

---

## 6. Buldyrev2010 シナリオのモジュール構成

`src/cmis_senario_games/scenarios/buldyrev2010/` 以下に当該論文向けロジックを集約する。

### 6.1 `network_definition.py`

- ER / Scale-free / Random regular の生成
- 実ネットワーク（イタリア停電）読み込みロジック

```python
def build_er_system(n: int, k_avg: float, seed: int) -> InterdependentSystem:
    ...


def build_sf_system(n: int, lambda_: float, k_min: int, seed: int) -> InterdependentSystem:
    ...


def build_real_italy_system(path_power: str,
                            path_comm: str,
                            path_dep: str) -> InterdependentSystem:
    ...
```

### 6.2 `config_schema.py`

- `configs/buldyrev2010/*.yaml` の構造を定義（pydantic / dataclasses での schema）。

```yaml
# configs/buldyrev2010/er_default.yaml
scenario_name: "buldyrev2010_er_protection"
game_type: "protection"
network:
  type: "er"
  num_nodes: 50000
  avg_degree: 4.0
  seed: 42
percolation:
  survival_prob: 0.8
  random_seed: 123
value_function:
  num_scenarios: 100
  performance_metric: "mcgc_size"
shapley:
  num_samples: 500
  random_seed: 999
```

### 6.3 `visualization.py`

- Buldyrev 的な図を再現：
  - (p) vs MCGC サイズ
  - (p) vs 存在確率（P∞）
  - ノード別 Shapley 値ヒートマップ（地理配置図 or 度数別）

```python
def plot_pc_curve(results_df: pd.DataFrame, output_path: str):
    """
    x: p, y: MCGC size / existence probability
    """


def plot_node_importance_shapley(phi: np.ndarray,
                                 network: InterdependentSystem,
                                 output_path: str):
    """
    ノード Shapley をネットワーク上に可視化。
    """
```

### 6.4 `postprocess_metrics.py`

- 実験結果から、
  - 推定された臨界値 (p_c)
  - 分布別脆弱性比較（ER vs SF vs RR）

等を集計する。

```python
def estimate_pc_from_results(results_df: pd.DataFrame) -> float:
    ...


def summarize_v_results(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    coalition / node ごとの v 値の一覧を生成。
    """
```

---

## 7. 実験ランナーと結果管理

`src/cmis_senario_games/core/experiment_runner.py`

- YAML の experiment 定義を読み込み、
- シナリオごとの network 構築
- `ValueFunction` 構築
- Shapley / lex-cel 実行
- 結果を `outputs/results/` 以下に保存
- 図を `outputs/figures/` に保存

```python
def run_experiment(experiment_config_path: str):
    """
    1. config ロード
    2. Scenario module 呼び出し
    3. v(S) 評価・Shapley 計算
    4. 結果を保存
    """
```

CLI 用のエントリポイント例：

```bash
python -m cmis_senario_games.run_experiment \
  --config experiments/buldyrev2010/node_importance_shapley.yaml
```

---

## 8. 共通出力フォーマット

### 8.1 v の結果一覧

`io_results.py` で統一フォーマットを定義：

```python
@dataclass
class ValueResult:
    game_type: GameType
    scenario_name: str
    coalition_id: str           # e.g. "node_42", "set_A", ...
    coalition_mask: np.ndarray
    v_value: float
```

CSV / Parquet 形式で保存：

`outputs/results/buldyrev2010/node_importance_shapley/v_values.parquet`

列例：

- `scenario_name`
- `game_type`
- `coalition_id`
- `v_value`

### 8.2 貢献度（Shapley / lex-cel）出力

`outputs/results/buldyrev2010/node_importance_shapley/contribution.parquet`

- `player_id`
- `phi_shapley`
- `rank_lexcel`
- オプションで degree, layer, centrality など説明変数も付与

---

## 9. 拡張：他フレームワーク・他論文パターンの組込み方針

- フレームワークは `GameType` と `ValueFunction` 実装で切り替え可能にする。
- Damage Reduction: `DamageReductionValue`
- Credit Allocation: `CreditAllocationValue`
- 論文パターンは `scenarios/<paper_short_name>/` として追加する。
- ネットワーク構造・パラメータの違いは `network_definition.py` と `config_schema.py` に閉じ込める。
- 可能な限り `core/` の再利用を徹底し、「論文ごとの固有ロジック」だけを scenario 側に寄せる。

Buldyrev2010 はその第1例として、

- 2層相互依存ネットワーク
- 防護型ゲーム（`PROTECTION`）
- 特性関数 = MCGC サイズの期待値

を実装する。

---

## 10. 実装順序（Buldyrev2010 パターン）

1. `core/` の基盤クラス・エンジン実装
   - `NetworkLayer`, `InterdependentSystem`
   - `percolation.py`, `cascade_engine.py`
   - `ValueFunction` 抽象, `contribution_shapley.py`
2. `scenarios/buldyrev2010/` 実装
   - `network_definition.py`（ER / SF / RR）
   - `value_protection.py`（防護型ゲーム）
   - `visualization.py`
3. `configs/buldyrev2010/*.yaml` の定義と `experiment_runner.py` からの実験実行
4. Shapley 値計算 + 可視化（ノード重要度ランキング）
5. `docs/scenario_buldyrev2010.md` で
   - 論文の数理モデル
   - 実装上の対応関係
   - パラメータのデフォルト値

を整理する。

以上を基本骨格とし、他の論文パターン（防護型・被害削減量・クレジット配分）も同一の構造・インターフェース上で拡張していく。

