from cmis_senario_games.core.game import ResilienceGame
from cmis_senario_games.core.graph import Edge, Graph, Node
from cmis_senario_games.core.fragility import FragilityParam
from cmis_senario_games.core.hazard import GmpeParam, HazardScenario
from cmis_senario_games.core.reinforcement import ReinforcementModel
from cmis_senario_games.core.simulation import SimulationConfig


def test_smoke_resilience_game_init():
    """最小構成で ResilienceGame が初期化できるかのスモークテスト。"""
    nodes = [Node(id=1, x=0.0, y=0.0), Node(id=2, x=1.0, y=0.0)]
    edges = [Edge(u=1, v=2)]
    graph = Graph(nodes=nodes, edges=edges, source_node_id=1, sink_node_id=2)

    frag_params = {
        1: FragilityParam(node_id=1, alpha=0.3, beta=0.6),
        2: FragilityParam(node_id=2, alpha=0.3, beta=0.6),
    }

    gmpe = GmpeParam(
        a=-1.0,
        b=0.5,
        c=-1.0,
        d=-0.01,
        h=5.0,
        sigma_inter=0.3,
        sigma_intra=0.4,
    )
    hazard = HazardScenario(
        magnitude=6.5,
        epicenter_x=0.0,
        epicenter_y=0.0,
        annual_rate=0.01,
    )
    reinforce = ReinforcementModel(alpha_factor=1.5, beta_factor=0.8)
    config = SimulationConfig(num_samples=10, random_seed=0)

    game = ResilienceGame(
        graph=graph,
        base_frag_params=frag_params,
        hazard=hazard,
        gmpe=gmpe,
        reinforce=reinforce,
        config=config,
    )

    assert 0.0 <= game.baseline_failure_probability <= 1.0

