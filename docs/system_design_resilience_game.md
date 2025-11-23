# レジリエンス協力ゲームモジュール 設計書

## 1. 概要

本プロジェクトは、論文中の仮想ライフラインネットワークを題材として、
ノード補強策の貢献度を協力ゲームとして評価するためのコアエンジンを提供する。

- 協力ゲームのプレイヤー: ノード型コンポーネント (N = {1, ..., n}, n=14 を基本想定)
- 提携 S: 事前に補強されたノード集合
- 特性関数 v(S): 補強なしに対するシステム失敗確率低減量

本設計書では、論文で定義されたモデルをプログラミング可能なレベルに落とし、
実装構成・データ構造・主要 API を整理する。

## 2. 要求仕様

### 2.1 機能要件

1. ネットワーク構造の表現
   - ノード・リンク・ソースノード・シンクノードを保持する。
2. ハザードと GMPE の表現
   - 地震マグニチュード、震源位置、年間発生率などを扱う。
   - GMPE パラメータおよび空間相関を考慮した PGA サンプル生成を行う。
3. Fragility モデル
   - 各ノードの fragility パラメータ (α, β) に基づき、損傷確率を評価する。
4. 補強モデル
   - 提携 S に含まれるノードの fragility を、指定された係数で更新する。
5. システム失敗判定
   - ノード故障状態のもとで、ソースノードとシンクノードの非連結性を判定する。
6. システム失敗確率 P_sys(S) の推定
   - モンテカルロシミュレーションにより P(F_sys | S) を推定する。
7. 特性関数 v(S) の計算
   - v(S) = P_sys(∅) - P_sys(S) を計算する API を提供する。
8. Shapley 値・シナジー指標への接続
   - ResilienceGame を汎用的な協力ゲームインターフェースとして、
     Shapley 値・相互作用指標の計算モジュールと接続可能にする。

### 2.2 非機能要件

- 研究用プロトタイプとして、再現性と拡張性を重視する。
- Python 3 系を対象とし、数値計算には NumPy / SciPy の利用を想定する。
- ネットワーク探索には networkx などのグラフライブラリ利用を許容する。

## 3. ドメインモデル

### 3.1 ネットワーク構造

```text
Node:
  id: int            # 1..n
  x, y: float        # ノード座標（震源距離計算に使用）

Edge:
  u: int             # ノードID
  v: int             # ノードID
  directed: bool     # 将来拡張用（現状は false を想定）

Graph:
  nodes: List[Node]
  edges: List[Edge]
  source_node_id: int    # 例: 2
  sink_node_id: int      # 例: 13
```

### 3.2 Fragility

```text
FragilityParam:
  node_id: int
  alpha: float    # median capacity (e.g. PGA)
  beta: float     # log-standard deviation
```

### 3.3 ハザード・GMPE

```text
GmpeParam:
  a, b, c, d, h: float   # GMPE 係数（論文式(17)に対応）
  sigma_inter: float     # σ_η (between-event)
  sigma_intra: float     # σ_ε (within-event)

HazardScenario:
  magnitude: float       # M
  epicenter_x, epicenter_y: float   # 震源位置
  annual_rate: float     # λ_H (年間発生率)
```

### 3.4 補強モデル

```text
ReinforcementModel:
  alpha_factor: float    # c_α > 1, median capacity の倍率
  beta_factor: float     # optional, c_β ∈ (0,1) など
```

### 3.5 シミュレーション設定

```text
SimulationConfig:
  num_samples: int       # モンテカルロサンプル数
  random_seed: int
  use_quasi_mc: bool     # 将来的に Sobol 等を利用するか
```

## 4. コアルーチン設計

### 4.1 PGA サンプル生成

```python
def sample_pga_for_all_nodes(
    graph: Graph,
    hazard: HazardScenario,
    gmpe: GmpeParam,
    rng: np.random.Generator
) -> Dict[int, float]:
    """
    各ノード i について PGA_i を 1 サンプル生成する。
    1. 各ノードの震源距離 R_i を計算
    2. GMPE により log PGA の平均 μ_i と標準偏差 σ_T を算出
    3. 空間相関モデルから共分散行列 Σ を構成
    4. 多変量正規乱数 z ~ N(0, Σ) をサンプリングし
       log PGA_i = μ_i + z_i として PGA を得る
    """
```

空間相関モデルの詳細（相関距離・関数形）は別途パラメータ化し、
初期実装では簡略化（例: 相関なし）も許容する。

### 4.2 ノード故障判定

```python
def compute_failure_prob_for_node(
    pga: float,
    frag: FragilityParam
) -> float:
    """
    fragility 曲線に基づき、P(E_i | PGA_i) を返す。
    P(E_i | PGA_i) = Φ((log PGA_i - log α_i) / β_i)
    """

def sample_node_failures(
    pga_samples: Dict[int, float],
    frag_params: Dict[int, FragilityParam],
    rng: np.random.Generator
) -> Dict[int, bool]:
    """
    各ノードについて Bernoulli 試行で故障/生存をサンプリングする。
    補強状態 S は frag_params 側に反映されている前提とする。
    """
```

### 4.3 システム失敗判定（連結性）

```python
def check_system_failure(
    graph: Graph,
    node_failed: Dict[int, bool]
) -> bool:
    """
    故障ノードを除いた有効グラフ上で、
    source_node_id から sink_node_id へのパスが存在しない場合に True を返す。
    実装は BFS / DFS あるいは networkx の連結性判定を用いる。
    """
```

## 5. システム失敗確率と特性関数

### 5.1 P_sys(S) の推定

```python
def estimate_system_failure_probability(
    coalition_S: Set[int],
    graph: Graph,
    base_frag_params: Dict[int, FragilityParam],
    hazard: HazardScenario,
    gmpe: GmpeParam,
    reinforce: ReinforcementModel,
    config: SimulationConfig
) -> float:
    """
    提携 S を補強した状態におけるシステム失敗確率 P_sys(S) を
    モンテカルロ法で推定する。
    """
```

処理ステップ:

1. 補強状態の反映
   - coalition_S に含まれるノードの fragility を ReinforcementModel に従って更新し、
     frag_params^S を構成する。
2. サンプリングループ
   - PGA サンプル生成 → ノード故障サンプル生成 → システム失敗判定。
   - 失敗回数 / サンプル数を P_sys(S) の推定値とする。

### 5.2 ResilienceGame クラス

```python
class ResilienceGame:
    def __init__(
        self,
        graph: Graph,
        frag_params: Dict[int, FragilityParam],
        hazard: HazardScenario,
        gmpe: GmpeParam,
        reinforce: ReinforcementModel,
        config: SimulationConfig,
    ):
        """
        ベースライン P_sys(∅) を初期化時に計算し保持する。
        """

    def payoff(self, coalition_S: Set[int]) -> float:
        """
        v(S) = P_sys(∅) - P_sys(S) を返す。
        """
```

## 6. 協力ゲームとの接続

ResilienceGame を一般的な協力ゲームインターフェースとして扱い、
以下のようなユーティリティを別モジュールにまとめる。

```python
def shapley_values(game: ResilienceGame) -> Dict[int, float]:
    """
    モンテカルロ法等により Shapley 値 φ_i(v) を近似計算する。
    実装は別モジュール coop.shapley で行う。
    """

def interaction_index(
    game: ResilienceGame,
    coalition_T: Set[int]
) -> float:
    """
    論文で定義したシナジー指標 / 相互作用指標 I(T) を計算する。
    実装は別モジュール coop.interaction_index で行う。
    """
```

## 7. ディレクトリ構成 (初期案)

```text
cmis_senario_games/
  README.md
  pyproject.toml (予定)
  requirements.txt (予定)
  docs/
    system_design_resilience_game.md
  src/
    cmis_senario_games/
      __init__.py
      core/
        __init__.py
        graph.py
        fragility.py
        hazard.py
        reinforcement.py
        simulation.py
        game.py
      coop/
        __init__.py
        shapley.py
        interaction_index.py
  tests/
    test_smoke.py (予定)
  examples/
    virtual_lifeline_network.ipynb (予定)
```

今後、β–η 図や critical scenarios に基づく拡張ゲーム v^{crit}(S) を追加する場合は、
`core/critical_scenarios.py` 等の専用モジュールとして切り出す方針とする。

