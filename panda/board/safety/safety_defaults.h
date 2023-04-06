const addr_checks default_rx_checks = {
  .check = NULL,
  .len = 0,
};

int default_rx_hook(CANPacket_t *to_push) {
  UNUSED(to_push);
  return true;
}

// *** no output safety mode ***

static const addr_checks* nooutput_init(int16_t param) {
  UNUSED(param);
  controls_allowed = false;
  relay_malfunction_reset();
  return &default_rx_checks;
}

static int nooutput_tx_hook(CANPacket_t *to_send, bool longitudinal_allowed) {
  UNUSED(to_send);
  UNUSED(longitudinal_allowed);
  return false;
}

static int nooutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return false;
}

bool check_mdps_bus1 = false;
static int default_fwd_hook(int bus_num, CANPacket_t *to_fwd) {
  int addr = GET_ADDR(to_fwd);  
  int bus_fwd = -1;

  if (true) {
      if (bus_num == 0) {
          bus_fwd = 2;
          if (check_mdps_bus1) bus_fwd = 12;
      }
      if (bus_num == 1) {
          if (addr == 593) check_mdps_bus1 = true;
          bus_fwd = -1;
          if (check_mdps_bus1) bus_fwd = 20;
      }
      if (bus_num == 2) {
          bus_fwd = 0;
          if (check_mdps_bus1) bus_fwd = 10;
      }
  }

  return bus_fwd;
}

const safety_hooks nooutput_hooks = {
  .init = nooutput_init,
  .rx = default_rx_hook,
  .tx = nooutput_tx_hook,
  .tx_lin = nooutput_tx_lin_hook,
  .fwd = default_fwd_hook,
};

// *** all output safety mode ***

// Enables passthrough mode where relay is open and bus 0 gets forwarded to bus 2 and vice versa
const uint16_t ALLOUTPUT_PARAM_PASSTHROUGH = 1;
bool alloutput_passthrough = false;

static const addr_checks* alloutput_init(int16_t param) {
  UNUSED(param);
  alloutput_passthrough = GET_FLAG(param, ALLOUTPUT_PARAM_PASSTHROUGH);
  controls_allowed = true;
  relay_malfunction_reset();
  return &default_rx_checks;
}

static int alloutput_tx_hook(CANPacket_t *to_send, bool longitudinal_allowed) {
  UNUSED(to_send);
  UNUSED(longitudinal_allowed);
  return true;
}

static int alloutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return true;
}

static int alloutput_fwd_hook(int bus_num, CANPacket_t *to_fwd) {
    int addr = GET_ADDR(to_fwd);
    int bus_fwd = -1;

  if (true || alloutput_passthrough) {
    if (bus_num == 0) {
      bus_fwd = 2;
      if (check_mdps_bus1) bus_fwd = 12;
    }
    if (bus_num == 1) {
        bus_fwd = -1;
        if (addr == 593) check_mdps_bus1 = true;
        if (check_mdps_bus1) bus_fwd = 20;
    }
    if (bus_num == 2) {
      bus_fwd = 0;
      if (check_mdps_bus1) bus_fwd = 10;
    }
  }

  return bus_fwd;
}

const safety_hooks alloutput_hooks = {
  .init = alloutput_init,
  .rx = default_rx_hook,
  .tx = alloutput_tx_hook,
  .tx_lin = alloutput_tx_lin_hook,
  .fwd = alloutput_fwd_hook,
};
