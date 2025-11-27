# Smith2019 → 貢献度評価フレームワーク写像

このファイルでは、Smith et al. (2019) のモデルを
本リポジトリの「プレイヤー → v(S) → Shapley」フレームワークに
どのように落とし込んでいるかを整理する。

## 1. ゲームタイプの選択

### 1.1 論文モデルの性質

Smith2019 は、

- 「全エッジが損傷した単層ネットワーク」
- 「各ステップで 1 本ずつエッジを復旧」
- 「復旧コスト = commodity deficit（需要未満足＋供給過多）の時間積分」

という **復旧戦略の評価問題** を扱っており、
事前防御（protection）や貢献度配分（credit allocation）は直接登場しない。

視点を変えると、

- どのエッジを早く復旧するか
- どの復旧順序が「総被害（commodity deficit）」を最も減らすか

という **ダメージ低減戦略の比較** と解釈できる。

### 1.2 GameType の提案

本リポジトリでゲームとして扱う場合、Smith2019 モデルは

- `GameType.DAMAGE_REDUCTION`

として扱うのが自然と考えられる。

- Protection 型:
  - 事前にノードやエッジを守り、災害時の故障確率を下げるモデル（Buldyrev2010 など）。
- DamageReduction 型（提案）:
  - 既に被害が発生している状況で、限られた復旧リソース（作業時間・人員）を
    どこに優先投入するかを選ぶモデル。
  - v(S) は「被害（コスト）の削減量」や「復旧効率」を表す。

Smith2019 の recovery percolation は、DamageReduction 型ゲームの特性関数 v(S) を近似する
ひとつの戦略クラスとみなせる。

## 2. プレイヤー定義

### 2.1 候補となるプレイヤー

Smith2019 では、復旧意思決定の単位は「どのエッジをいつ修復するか」であるため、

- プレイヤー = エッジ（送電線）

と解釈するのが素直である。

他の可能性としては：

- プレイヤー = 供給ノード（発電所）
- プレイヤー = 需要ノード（クリティカル負荷）

などがありうるが、recovery percolation の直接の意思決定単位はエッジなので、
ここではエッジをプレイヤーとする。

### 2.2 コアリションの意味

- プレイヤー集合 S を「優先的に復旧対象とするエッジ群」と解釈する。
- `coalition[e] = True` であれば、「エッジ e は早期に復旧に投入することが許されている」と読む。

実装上のイメージ：

- エッジをインデックス 0..E-1 で番号付けし、
- `coalition` を長さ E のブールベクトルとする。
- v(S) の評価時には、
  - S に含まれるエッジのみを候補集合とする recovery strategy を想定したり、
  - あるいは「S に含まれるエッジは先に修復される」ような順序制約を課す、などが考えられる。

どのバリエーションを採用するかは、Smith2019 シナリオをどの程度忠実に再現したいかに依存するが、
いずれの場合も「プレイヤー＝エッジ」「コアリション＝早期復旧対象エッジの集合」という解釈で一貫している。

## 3. 特性関数 v(S) の定義

### 3.1 性能指標

Smith2019 の性能指標は主に 2 つ：

- \(D(t)\): 時刻 t における総 commodity deficit（需要未満足＋供給過多の絶対値の総和）。
- \(C_M = \sum_t D(t)\): 復旧期間全体に渡る commodity deficit の積分（復旧コスト）。

ゲーム理論側では、

- 「総コストが小さいほど価値が高い」と解釈して、

\[
v(S) = - \mathbb{E}[C_M(S)]
\]

のような定義（**コストの負値**を価値とみなす）を採用するのが自然である。

ここで \(C_M(S)\) は、

- coalition S を前提とした復旧戦略（例えば S のエッジを優先する recovery percolation）を適用したときの総コスト。

### 3.2 確率構造

Smith2019 では、初期被害パターンや需要分布にランダム性が含まれるケースも扱う。
ゲームとして一般化するにあたっては、初期状態や需要分布を確率変数 \(\omega\) とみなし、

\[
v(S) = - \mathbb{E}_\omega [C_M(S; \omega)]
\]

とすることで、Buldyrev2010 と同様に **期待値ベースの特性関数**として統一できる。

### 3.3 実装クラスのイメージ

現時点では Smith2019 シナリオのコード実装は存在しないが、
Buldyrev2010 の `BuldyrevProtectionValue` に倣うと、次のような `ValueFunction` を想定できる：

```python
@dataclass
class SmithRecoveryConfig:
    demand: DemandParams
    num_scenarios: int
    recovery_rule: RecoveryRule  # td-NDP or recovery percolation


class SmithDamageReductionValue(ValueFunction):
    game_type = GameType.DAMAGE_REDUCTION

    def __init__(self, network: NetworkLayer, config: SmithRecoveryConfig):
        self.network = network
        self.config = config

    def evaluate(self, coalition: np.ndarray) -> float:
        # coalition[e] = True なエッジを優先復旧候補とする
        # Monte Carlo により v(S) ≈ -E[C_M(S)] を推定
        ...
```

どの復旧ルールを採用するか（td-NDP か recovery percolation か）は、
シナリオの目的（精度 vs 計算量）に応じて切り替え可能とするイメージ。

## 4. モデル構成要素と core モジュールの対応

### 4.1 コアモデルとの対応

Smith2019 のネットワークは単層であるため、本リポジトリでは：

- ネットワーク構造:
  - → `NetworkLayer` 単体、または `MultiLayerNetwork(layers={"G": layer})` として格納。
- 依存関係:
  - レイヤ間依存は扱わないため、`DependencyMapping` は不要（またはダミー）。
- 初期故障:
  - Smith2019 の基本設定は「全エッジ損傷」だが、
    より一般的には `PercolationParams` で部分損傷を表現することも可能。
- カスケード:
  - Buldyrev2010 のような `run_cascade` を用いた相互依存カスケードは存在せず、
    復旧シミュレーションはシナリオ固有の「復旧ルール」（recovery percolation / td-NDP）として別実装になる。
- v(S):
  - これらを組み合わせた `SmithDamageReductionValue.evaluate(coalition)` が特性関数となる。

### 4.2 Recovery percolation / td-NDP の位置づけ

Smith2019 での 2 つの復旧モデル：

- td-NDP（最適復旧）:
  - 混合整数計画による高精度だが高コストなベンチマーク。
  - 小規模ネットワークでのみ現実的。
- Recovery percolation:
  - commodity deficit を減らすようにエッジを貪欲に選ぶ競合パーコレーション。
  - O(EM) の計算量で大規模ネットワークにも適用可能。

本フレームワークに組み込む場合、

- シナリオ内部で「どの復旧ルールを使うか」を切り替え可能にし、
- デフォルトでは計算量が軽い recovery percolation を使って v(S) を評価する、

といった設計が自然である。

## 5. YAML 設定との対応

- `configs/smith2019/*.yaml`（将来追加想定）:
  - `network`: 実データ（Shelby County）または合成電力網の構成。
  - `demand`: ノードごとの \(d_i\) 分布や供給ノード割合。
  - `recovery`: 復旧戦略（td-NDP か recovery percolation か）、M の値など。
  - `value_function`: Monte Carlo サンプル数や評価指標（総コスト、t90 など）。
  - `shapley`: Shapley サンプリング設定。

- `experiments/smith2019/*.yaml`（将来追加想定）:
  - `scenario_config` でどのネットワーク・需要分布・復旧ルールを使うか指定。
  - `mode` で、単一シナリオ評価・構造パラメータスイープ等を切り替え。
  - `output_dir` / `figure_dir` を通じて、コスト曲線やエッジ貢献度ランキングを出力。

このような写像を通じて、

- 「どの送電線（エッジ）を優先的に復旧すべきか」
- 「ネットワーク構造や需要分布が、エッジ単位のレジリエンス貢献度にどう影響するか」

といった Smith2019 型の復旧問題を、Buldyrev2010 と同じ貢献度評価フレームワーク上で扱う設計方針を示している。

## 6. 図解（Mermaid）

### 6.1 Smith2019 モデル → フレームワーク対応図

```mermaid
flowchart LR
    subgraph PaperModel[Smith2019 モデル]
        G[単層ネットワーク G(N,E)]
        d[ノード需要・供給 d_i]
        RecProc[復旧ルール<br/>(td-NDP / Recovery percolation)]
    end

    subgraph Framework[cmis_senario_games フレームワーク]
        GT[GameType.DAMAGE_REDUCTION]
        Players[プレイヤー集合 S<br/>(エッジ集合)]
        vS[特性関数 v(S) = -E[C_M(S)]]
        VF[ValueFunction 実装<br/>SmithDamageReductionValue]
    end

    G --> RecProc
    d --> RecProc
    RecProc -->|復旧順序によりコスト C_M(S)| vS

    G --> Players
    Players --> vS
    vS --> VF
    GT --> VF
```

### 6.2 v(S) 評価の概念シーケンス

```mermaid
sequenceDiagram
    autonumber
    participant Caller as 呼び出し側<br/>(Shapley 等)
    participant VF as SmithDamageReductionValue
    participant Sim as 復旧シミュレータ<br/>(td-NDP/Recovery percolation)

    Caller->>VF: evaluate(coalition S)
    activate VF
    VF->>VF: total = 0

    loop num_scenarios 回
        VF->>Sim: coalition S と乱数シナリオ ω を指定して<br/>復旧をシミュレート
        Sim-->>VF: コスト C_M(S; ω) = Σ_t D(t)
        VF->>VF: total += C_M(S; ω)
    end

    VF->>VF: v(S) = - total / num_scenarios
    VF-->>Caller: v(S)
    deactivate VF
```
