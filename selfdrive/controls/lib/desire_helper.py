from cereal import log
from common.conversions import Conversions as CV
from common.realtime import DT_MDL
from common.conversions import Conversions as CV
from common.params import Params

AUTO_LCA_START_TIME = 0.2

LaneChangeState = log.LateralPlan.LaneChangeState
LaneChangeDirection = log.LateralPlan.LaneChangeDirection

#LANE_CHANGE_SPEED_MIN = 15 * CV.MPH_TO_MS
LANE_CHANGE_SPEED_MIN = 1 * CV.KPH_TO_MS # 30 * CV.MPH_TO_MS
TURN_CHANGE_SPEED_MAX = 30 * CV.KPH_TO_MS # 30 * CV.MPH_TO_MS
LANE_CHANGE_TIME_MAX = 10.

DESIRES = {
  LaneChangeDirection.none: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.none,
  },
  LaneChangeDirection.left: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.laneChangeLeft,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.laneChangeLeft,
  },
  LaneChangeDirection.right: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.laneChangeRight,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.laneChangeRight,
  },
}
DESIRES_TURN = {
  LaneChangeDirection.none: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.none,
  },
  LaneChangeDirection.left: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.turnLeft,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.none,
  },
  LaneChangeDirection.right: {
    LaneChangeState.off: log.LateralPlan.Desire.none,
    LaneChangeState.preLaneChange: log.LateralPlan.Desire.none,
    LaneChangeState.laneChangeStarting: log.LateralPlan.Desire.turnRight,
    LaneChangeState.laneChangeFinishing: log.LateralPlan.Desire.none,
  },
}


class DesireHelper:
  def __init__(self):
    self.lane_change_state = LaneChangeState.off
    self.lane_change_direction = LaneChangeDirection.none
    self.lane_change_timer = 0.0
    self.lane_change_ll_prob = 1.0
    self.keep_pulse_timer = 0.0
    self.prev_one_blinker = False
    self.desire = log.LateralPlan.Desire.none
    self.turnControl = False

    self.lane_change_enabled = True #Params().get_bool('LaneChangeEnabled')
    self.auto_lane_change_enabled = True #Params().get_bool('AutoLaneChangeEnabled')
    self.auto_lane_change_timer = 0.0
    self.prev_torque_applied = False

  def update(self, carstate, lateral_active, lane_change_prob, md, autoTurnControl, turn_prob):
    v_ego = carstate.vEgo
    one_blinker = carstate.leftBlinker != carstate.rightBlinker
    if autoTurnControl:
      below_lane_change_speed = v_ego < LANE_CHANGE_SPEED_MIN
    else:
      below_lane_change_speed = v_ego < TURN_CHANGE_SPEED_MAX

    left_road_edge = -md.roadEdges[0].y[0]
    right_road_edge = md.roadEdges[1].y[0]

    laneChangeTimeMax = LANE_CHANGE_TIME_MAX if not self.turnControl else 60

    if not lateral_active or self.lane_change_timer > laneChangeTimeMax: #LANE_CHANGE_TIME_MAX:
      self.lane_change_state = LaneChangeState.off
      self.lane_change_direction = LaneChangeDirection.none
    else:
      # LaneChangeState.off
      # 아무것도 안하고, 깜박이켜져있고(자동차선인경우 계속켜져있어도 작동), 차선변경 제한속도까지...=> 레인체인지상태:preLaneChange상태로 변경
      if self.lane_change_state == LaneChangeState.off and one_blinker and (not self.prev_one_blinker or autoTurnControl>0) and not below_lane_change_speed:
        self.lane_change_state = LaneChangeState.preLaneChange
        self.lane_change_ll_prob = 1.0

      # LaneChangeState.preLaneChange
      elif self.lane_change_state == LaneChangeState.preLaneChange:
        # Set lane change direction
        self.lane_change_direction = LaneChangeDirection.left if \
          carstate.leftBlinker else LaneChangeDirection.right

        torque_applied = carstate.steeringPressed and \
                         ((carstate.steeringTorque > 0 and self.lane_change_direction == LaneChangeDirection.left) or
                          (carstate.steeringTorque < 0 and self.lane_change_direction == LaneChangeDirection.right)) or \
                        self.auto_lane_change_enabled and \
                       (AUTO_LCA_START_TIME+0.25) > self.auto_lane_change_timer > AUTO_LCA_START_TIME

        blindspot_detected = ((carstate.leftBlindspot and self.lane_change_direction == LaneChangeDirection.left) or
                              (carstate.rightBlindspot and self.lane_change_direction == LaneChangeDirection.right))

        road_edge_detected = (((left_road_edge < 3.5) and self.lane_change_direction == LaneChangeDirection.left) or
                              ((right_road_edge < 3.5) and self.lane_change_direction == LaneChangeDirection.right))

        #if v_ego < TURN_CHANGE_SPEED_MAX and autoTurnControl>0:
        if autoTurnControl>0:
            if (road_edge_detected or v_ego < TURN_CHANGE_SPEED_MAX):  # 자동턴모드: 도로경계이거나 25키로보다 작을땐... turnControl시작
                road_edge_detected = False
                self.turnControl = True
            else:
                self.turnControl = False
        else:
            self.turnControl = False

        if not one_blinker or below_lane_change_speed:
          self.lane_change_state = LaneChangeState.off
        elif torque_applied and (not blindspot_detected or self.prev_torque_applied) and not road_edge_detected:
          self.lane_change_state = LaneChangeState.laneChangeStarting
        elif torque_applied and blindspot_detected and self.auto_lane_change_timer != 10.0:
          self.auto_lane_change_timer = 10.0
        elif not torque_applied and self.auto_lane_change_timer == 10.0 and not self.prev_torque_applied:
          self.prev_torque_applied = True

      # LaneChangeState.laneChangeStarting
      elif self.lane_change_state == LaneChangeState.laneChangeStarting:
        # fade out over .5s
        self.lane_change_ll_prob = max(self.lane_change_ll_prob - 2 * DT_MDL, 0.0)

        # 98% certainty
        if self.turnControl:
            if turn_prob < 0.02 and self.lane_change_ll_prob < 0.01:
              self.lane_change_state = LaneChangeState.laneChangeFinishing
        else:
            if lane_change_prob < 0.02 and self.lane_change_ll_prob < 0.01:
              self.lane_change_state = LaneChangeState.laneChangeFinishing

      # LaneChangeState.laneChangeFinishing
      elif self.lane_change_state == LaneChangeState.laneChangeFinishing:
        # fade in laneline over 1s
        self.lane_change_ll_prob = min(self.lane_change_ll_prob + DT_MDL, 1.0)

        if self.turnControl:
            if self.lane_change_ll_prob > 0.99:
                self.lane_change_direction = LaneChangeDirection.none
            if one_blinker: #깜박이 켜고 있으면.... 아직 턴하고 있는중... 이때 preLaneChange로 넘어가면 계속 턴하려고 함...
                pass
            else:
                self.lane_change_state = LaneChangeState.off
        else:
            if self.lane_change_ll_prob > 0.99:
                self.lane_change_direction = LaneChangeDirection.none
            if one_blinker:
                self.lane_change_state = LaneChangeState.preLaneChange
            else:
                self.lane_change_state = LaneChangeState.off

    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.preLaneChange):
      self.lane_change_timer = 0.0
    else:
      self.lane_change_timer += DT_MDL

    if self.lane_change_state == LaneChangeState.off:
      self.auto_lane_change_timer = 0.0
      self.prev_torque_applied = False
    elif self.auto_lane_change_timer < (AUTO_LCA_START_TIME+0.25): # stop afer 3 sec resume from 10 when torque applied
      self.auto_lane_change_timer += DT_MDL

    self.prev_one_blinker = one_blinker

    self.desire = DESIRES_TURN[self.lane_change_direction][self.lane_change_state] if self.turnControl else DESIRES[self.lane_change_direction][self.lane_change_state]

    # Send keep pulse once per second during LaneChangeStart.preLaneChange
    if self.lane_change_state in (LaneChangeState.off, LaneChangeState.laneChangeStarting):
      self.keep_pulse_timer = 0.0
    elif self.lane_change_state == LaneChangeState.preLaneChange:
      self.keep_pulse_timer += DT_MDL
      if self.keep_pulse_timer > 1.0:
        self.keep_pulse_timer = 0.0
      elif self.desire in (log.LateralPlan.Desire.keepLeft, log.LateralPlan.Desire.keepRight):
        self.desire = log.LateralPlan.Desire.none
