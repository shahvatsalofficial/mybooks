# case_studies/cs04_mcts_logistics_agent.py
"""
Case Study 04: Real-Time Logistics Fleet Rerouting via MCTS.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import math
import time
import random
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCTSLogisticsAgent")

# ============================================================================
# 1. DOMAIN SCHEMAS & MCTS TREE STRUCTURE
# ============================================================================

class DeliveryStop(BaseModel):
    stop_id: str
    lat: float
    lon: float
    time_window_end_epoch: int
    penalty_cost_per_min: float = 15.0

class FleetState(BaseModel):
    vehicle_id: str
    current_lat: float
    current_lon: float
    remaining_stops: List[DeliveryStop]
    elapsed_time_min: float = 0.0
    accumulated_penalty: float = 0.0

class MCTSNode:
    def __init__(self, state: FleetState, parent: Optional['MCTSNode'] = None, action: Optional[DeliveryStop] = None):
        self.state = state
        self.parent = parent
        self.action = action  # The stop chosen to visit next
        self.children: List['MCTSNode'] = []
        self.visits: int = 0
        self.total_value: float = 0.0

    def is_fully_expanded(self) -> bool:
        return len(self.children) == len(self.state.remaining_stops)

    def select_best_child(self, c_param: float = 1.414) -> 'MCTSNode':
        """Selects child node using Upper Confidence Bound for Trees (UCT)."""
        best_score = -float('inf')
        best_child = None
        for child in self.children:
            if child.visits == 0:
                return child
            # UCT Formula: Exploitation + Exploration
            exploitation = child.total_value / child.visits
            exploration = c_param * math.sqrt(math.log(self.visits) / child.visits)
            uct_score = exploitation + exploration
            if uct_score > best_score:
                best_score = uct_score
                best_child = child
        return best_child or self.children[0]

# ============================================================================
# 2. MONTE CARLO TREE SEARCH PLANNER
# ============================================================================

class MCTSPlanner:
    def __init__(self, max_iterations: int = 500, max_time_sec: float = 1.0):
        self.max_iterations = max_iterations
        self.max_time_sec = max_time_sec

    def _estimate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Euclidean distance approximation in minutes (1 unit = 10 mins)."""
        dist = math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
        return dist * 100.0

    def _simulate_rollout(self, state: FleetState) -> float:
        """Fast heuristic simulation of remaining route execution."""
        curr_lat, curr_lon = state.current_lat, state.current_lon
        curr_time = state.elapsed_time_min
        total_penalty = state.accumulated_penalty
        stops = list(state.remaining_stops)
        random.shuffle(stops)  # Random rollout policy

        for stop in stops:
            travel_time = self._estimate_distance(curr_lat, curr_lon, stop.lat, stop.lon)
            curr_time += travel_time
            curr_lat, curr_lon = stop.lat, stop.lon
            # Calculate SLA penalty if late
            if curr_time > 120:  # 2-hour window limit
                late_mins = curr_time - 120
                total_penalty += late_mins * stop.penalty_cost_per_min

        # Inverse reward (higher reward for lower penalty)
        reward = 1000.0 / (1.0 + total_penalty)
        return reward

    def plan_optimal_route(self, initial_state: FleetState) -> List[str]:
        logger.info(f"⚡ [MCTS Planner] Executing tree rollouts for vehicle {initial_state.vehicle_id}...")
        root = MCTSNode(state=initial_state)
        start_time = time.time()

        for iteration in range(self.max_iterations):
            if (time.time() - start_time) >= self.max_time_sec:
                logger.info(f"⏱️ [MCTS Planner] Time limit reached ({self.max_time_sec}s). Executed {iteration} iterations.")
                break

            # 1. Selection
            node = root
            while node.is_fully_expanded() and node.children:
                node = node.select_best_child()

            # 2. Expansion
            if not node.is_fully_expanded():
                unvisited_stops = [
                    s for s in node.state.remaining_stops 
                    if s.stop_id not in [c.action.stop_id for c in node.children if c.action]
                ]
                if unvisited_stops:
                    chosen_stop = random.choice(unvisited_stops)
                    remaining = [s for s in node.state.remaining_stops if s.stop_id != chosen_stop.stop_id]
                    dist = self._estimate_distance(node.state.current_lat, node.state.current_lon, chosen_stop.lat, chosen_stop.lon)
                    new_state = FleetState(
                        vehicle_id=node.state.vehicle_id,
                        current_lat=chosen_stop.lat,
                        current_lon=chosen_stop.lon,
                        remaining_stops=remaining,
                        elapsed_time_min=node.state.elapsed_time_min + dist,
                        accumulated_penalty=node.state.accumulated_penalty
                    )
                    child_node = MCTSNode(state=new_state, parent=node, action=chosen_stop)
                    node.children.append(child_node)
                    node = child_node

            # 3. Simulation
            reward = self._simulate_rollout(node.state)

            # 4. Backpropagation
            curr = node
            while curr:
                curr.visits += 1
                curr.total_value += reward
                curr = curr.parent

        # Extract optimal route path
        optimal_path = []
        curr = root
        while curr.children:
            best_child = max(curr.children, key=lambda c: c.visits)
            if best_child.action:
                optimal_path.append(best_child.action.stop_id)
            curr = best_child

        return optimal_path

# ============================================================================
# 3. LANGGRAPH AGENT INTEGRATION
# ============================================================================

class LogisticsAgentState(BaseModel):
    fleet_state: FleetState
    recommended_route: List[str] = Field(default_factory=list)
    computation_time_ms: float = 0.0
    status: str = "INITIALIZED"

def mcts_routing_node(state: LogisticsAgentState) -> Dict[str, Any]:
    t0 = time.time()
    planner = MCTSPlanner(max_iterations=1000, max_time_sec=1.2)
    optimal_route = planner.plan_optimal_route(state.fleet_state)
    elapsed_ms = round((time.time() - t0) * 1000, 2)
    logger.info(f" [MCTS Routing Node] Optimal route calculated in {elapsed_ms}ms: {optimal_route}")
    return {
        "recommended_route": optimal_route,
        "computation_time_ms": elapsed_ms,
        "status": "ROUTE_OPTIMIZED"
    }

def build_logistics_graph():
    builder = StateGraph(LogisticsAgentState)
    builder.add_node("mcts_routing", mcts_routing_node)
    builder.set_entry_point("mcts_routing")
    builder.add_edge("mcts_routing", END)
    return builder.compile()

if __name__ == "__main__":
    stops = [
        DeliveryStop(stop_id="STOP_A", lat=40.7128, lon=-74.0060, time_window_end_epoch=1000),
        DeliveryStop(stop_id="STOP_B", lat=40.7589, lon=-73.9851, time_window_end_epoch=1100),
        DeliveryStop(stop_id="STOP_C", lat=40.7061, lon=-74.0088, time_window_end_epoch=1050),
        DeliveryStop(stop_id="STOP_D", lat=40.7829, lon=-73.9654, time_window_end_epoch=1200),
    ]
    initial_fleet = FleetState(vehicle_id="VAN-402", current_lat=40.7306, current_lon=-73.9352, remaining_stops=stops)
    agent_state = LogisticsAgentState(fleet_state=initial_fleet)
    
    graph = build_logistics_graph()
    res = graph.invoke(agent_state)
    print(f"\nFinal Status: {res['status']}")
    print(f"Optimal Sequence: {res['recommended_route']}")
    print(f"Execution Latency: {res['computation_time_ms']} ms")
