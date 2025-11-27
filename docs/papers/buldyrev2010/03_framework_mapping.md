# Buldyrev2010 → 貢献度評価フレームワーク写像

このファイルでは、Buldyrev2010 のモデルを
本リポジトリの「プレイヤー → v(S) → Shapley」フレームワークに
どのように落とし込んでいるかを整理する。

## 1. ゲームタイプの選択

### 1.1 論文モデルの解釈

Buldyrev2010 は、**与えられた interdependent networks がランダム攻撃に対してどれだけ脆いか**を
解析する論文であり、ゲーム理論は直接は登場しない。

- 主眼は「初期攻撃の強さ \(1-p\) に対して、MCGC の相対サイズ \(P_\infty(p)\) がどう変化するか」。
- プレイヤーやコアリションは明示されず、全体システムのロバスト性を評価している。

本リポジトリでは、これを **防御投資ゲーム** として解釈する：

- 各ノード（あるいはノードペア）に防護資源を割り当てるプレイヤーがいて、
- 防護されたノードは初期攻撃から守られる（常に percolation を生き残る）、
- その結果として「最終的にどれだけ大きな MCGC が保たれるか」を価値とみなす。

### 1.2 GameType の選択

この解釈に基づき、Buldyrev2010 シナリオは

- `GameType.PROTECTION`（防護型ゲーム）

として実装される。

- 「攻撃が与えられている状況で、どこを守るか」を選ぶゲーム。
- 特性関数 v(S) は「防御集合 S を選んだときのシステムの残存性能（MCGC サイズ）の期待値」を表す。

## 2. プレイヤー定義

### 2.1 候補となるプレイヤー

論文モデルをゲームに落とす際、プレイヤーの候補として次が考えられる：

- A 層ノード（電力ノード）
- B 層ノード（通信ノード）
- A/B ノードペア \((A_i, B_j)\)

Buldyrev2010 の枠組みでは A/B が 1:1 依存しているため、

- \((A_i, B_i)\)（あるいは \((A_i, B_{\text{dep}(i)})\)）という「ノードペア」を 1 単位として扱うのが自然。

### 2.2 本実装での選択

本リポジトリの `BuldyrevProtectionValue` では、

- プレイヤー ID i = A 層のノード i
- その背後に「依存先の B 層ノード」がペアとして紐づいている

という形でプレイヤーを定義する。

- `coalition: np.ndarray[bool]`（長さ N）の i 番目は、
  - 「A 層ノード i と、それに依存する B 層ノードのペアを防御するかどうか」を表す。
- `coalition[i] = True` のとき：
  - percolation でどれだけ攻撃されても、そのノード ID i は **初期故障から必ず生き残る**。
  - ただし、その後のカスケード（依存伝播＋連結性フィルタ）で落ちる可能性はある。

このように、プレイヤー = 「ノード ID i に対応するノードペア」として扱いつつ、
実装上は A 層のインデックスをプレイヤー ID として使っている。

## 3. 特性関数 v(S) の定義

### 3.1 論文側の指標との対応

論文では、ある攻撃レベル \(1-p\) のもとで

- カスケード後に残る MCGC の相対サイズ \(P_\infty(p)\)

を主な性能指標としている。これは本リポジトリの `m_infty` に対応する。

ゲーム理論側では、攻撃レベル（percolation の \(p\)）を固定したうえで、

- 防御集合 S（プレイヤー集合）を変化させたときの
  - MCGC の相対サイズ（カスケード後の残存規模）
  - その期待値

を特性関数 v(S) として定義する。

### 3.2 数式レベルの定義

防御集合 S を与えるブールベクトル `coalition` に対して、

- 1 回のシミュレーションで得られる MCGC の相対サイズを \(F_S(\omega)\) とする。
  - \(\omega\) は percolation の乱数シナリオ（どのノードが初期攻撃で落ちるか）。
- その期待値を

\[
v(S) = \mathbb{E}_\omega \left[ F_S(\omega) \right]
\]

として特性関数とする。

実装では Monte Carlo 平均として近似する：

```python
total = 0.0
for _ in range(num_scenarios):
    alive0 = sample_initial_failure(system, percolation_params)
    alive0[coalition] = True      # S に含まれるノードは必ず初期状態で alive
    result = run_cascade(system, alive0)
    total += result.m_infty       # = MCGC の相対サイズ
v_S = total / num_scenarios
```

### 3.3 性能指標の選択肢

デフォルトでは v(S) は `m_infty` を性能指標としているが、
他の指標を用いる拡張も考えられる：

- MCGC のノード数ではなく、リンク数や重み付きサイズを使う。
- 特定の重要ノード（例: 高需要エリア）に属するノードが何割残るか、など。

本シナリオでは Buldyrev2010 に忠実に、
**「全ノードに対する MCGC の相対サイズ」**を採用している。

## 4. モデル構成要素と core モジュールの対応

### 4.1 対応表

論文の概念と、本リポジトリの core モジュールの対応は概ね次の通り。

- 2 層ネットワーク A/B
  - → `MultiLayerNetwork`（`core/network_model.py`）
  - 各層は `NetworkLayer(name="A" or "B", num_nodes=N, edges=...)`
- 1:1 の相互依存 \(A_i \Leftrightarrow B_i\)
  - → `DependencyMapping(dep_A_to_B, dep_B_to_A)`（`core/interdependency.py`）
- 初期攻撃（ランダムに 1−p のノードを除去）
  - → `PercolationParams(survival_prob=p)` + `sample_initial_failure(system, params)`
- カスケード故障（A→B, B→A 伝播 + 各層で GCC のみ残す反復）
  - → `run_cascade(system, initial_alive_mask)`（`core/cascade_engine.py`）
- giant mutually connected component (MCGC)
  - → `CascadeResult.final_alive_mask` および `CascadeResult.m_infty`
- 相転移解析（p-sweep）
  - → 将来的には `er_pc_sweep.yaml` などの実験定義 + postprocess

### 4.2 Buldyrev2010 固有のシナリオ実装

Buldyrev2010 固有のロジックは `scenarios/buldyrev2010/` に配置される：

- `network_definition.py`
  - ER / SF / real_italy など、論文で扱うネットワークファミリーを構築。
  - ER: `build_er_system` → 2 層 ER + identity 依存。
  - SF: `build_sf_system` → 2 層 BA 近似 + identity 依存。
  - Italy case: `build_real_italy_system` → 実データから 2 層ネットワーク + 依存マッピングを構築。
- `value_protection.py`
  - `BuldyrevProtectionConfig`, `BuldyrevProtectionValue` を定義し、
    percolation + run_cascade を組み合わせて v(S) を実装。
- `visualization.py`
  - 論文の図に対応する可視化（p vs MCGC、ノード重要度、カスケード例など）を実装。

## 5. YAML 設定との対応

### 5.1 シナリオ設定（configs/buldyrev2010/*.yaml）

`configs/buldyrev2010/` には、Buldyrev2010 の各種設定が YAML として定義される。

代表例：

- `er_default.yaml`
  - 2 層 ER ネットワーク（平均次数 \(\langle k \rangle\) を論文の値に合わせる）、
    生残確率 \(p\)、Monte Carlo サンプル数などを設定。
- `sf_default.yaml`
  - 2 層スケールフリーネットワーク（\(\lambda\), \(k_{\min}\) 等）を論文のパラメータに合わせる。
- `italy_case_study.yaml`
  - イタリア電力 + 通信ネットワークの CSV パスと、
    percolation / value_function / shapley のデフォルト値を定義。

これらは `BuldyrevExperimentConfig`（`config_schema.py`）に読み込まれ、

- `network` → どのビルダ（ER/SF/real_italy）を使うか
- `percolation` → 論文の \(p\) に対応
- `value_function` → Monte Carlo サンプル数・性能指標の指定
- `shapley` → Shapley 推定のサンプリングパラメータ

として利用される。

### 5.2 実験定義（experiments/buldyrev2010/*.yaml）

`experiments/buldyrev2010/` には、「どのシナリオ設定をどう走らせるか」が記述される。

- `er_pc_sweep.yaml`
  - 複数の \(p\)（survival_prob）をスイープし、
    \(P_\infty(p)\) 曲線を再現する実験（論文の Fig. 3 に相当）。
- `node_importance_shapley.yaml`
  - 固定された \(p\)・ネットワークのもとで、各ノードの Shapley 値を推定し、
    「どのノードを守るべきか」のランキングを出す実験。
- `italy_case_basic_run.yaml`
  - Italy case の単純な v(S) 評価（小規模ネットワークでは 2^N 全列挙）と、
    カスケード履歴の保存。

論文そのものは Shapley 等のゲーム理論指標を扱っていないが、

- **「interdependent networks 上のロバストネス・モデル」**として Buldyrev2010 を採用し、
- 本リポジトリの貢献度評価フレームワークに組み込むことで、
  - どのノード（/ノードペア）の防御が MCGC をどれだけ改善するか
  - どのノードを優先的に強靭化すべきか

といった「配分・優先順位づけ」の議論ができるようになっている。
