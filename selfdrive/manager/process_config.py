import os

from cereal import car
from common.params import Params
from selfdrive.hardware import EON, TICI, PC
from selfdrive.manager.process import PythonProcess, NativeProcess, DaemonProcess

WEBCAM = os.getenv("USE_WEBCAM") is not None

#dp_dm = Params().get_bool('ShowDmInfo')
dp_dm = int(Params().get("ShowDmInfo", encoding="utf8")) >= 0
def driverview(started: bool, params: Params, CP: car.CarParams) -> bool:
  return dp_dm and params.get_bool("IsDriverViewEnabled")  # type: ignore
def ublox(started, params, CP: car.CarParams) -> bool:
  use_ublox = True # ublox_available()
  params.put_bool("UbloxAvailable", use_ublox)
  return started and use_ublox
procs = [
  #DaemonProcess("manage_athenad", "selfdrive.athena.manage_athenad", "AthenadPid"),
  # due to qualcomm kernel bugs SIGKILLing camerad sometimes causes page table corruption
  NativeProcess("camerad", "selfdrive/camerad", ["./camerad"], unkillable=True, callback=driverview),
  NativeProcess("clocksd", "selfdrive/clocksd", ["./clocksd"]),
  #NativeProcess("proclogd", "selfdrive/proclogd", ["./proclogd"]),
  #PythonProcess("logmessaged", "selfdrive.logmessaged", offroad=True),
  #PythonProcess("timezoned", "selfdrive.timezoned", enabled=TICI),
  #NativeProcess("logcatd", "selfdrive/logcatd", ["./logcatd"]),
  #NativeProcess("loggerd", "selfdrive/loggerd", ["./loggerd"]),
  NativeProcess("modeld", "selfdrive/modeld", ["./modeld"]),
  #NativeProcess("navd", "selfdrive/ui/navd", ["./navd"], enabled=(PC or TICI), offroad=True),
  NativeProcess("ui", "selfdrive/ui", ["./ui"], offroad=True, watchdog_max_dt=(5 if TICI else None)),
  NativeProcess("soundd", "selfdrive/ui/soundd", ["./soundd"], offroad=True),
  NativeProcess("locationd", "selfdrive/locationd", ["./locationd"]),
  NativeProcess("boardd", "selfdrive/boardd", ["./boardd"], enabled=False),
  PythonProcess("calibrationd", "selfdrive.locationd.calibrationd"),
  PythonProcess("torqued", "selfdrive.locationd.torqued"),
  PythonProcess("controlsd", "selfdrive.controls.controlsd"),
  #PythonProcess("deleter", "selfdrive.loggerd.deleter", offroad=True),
  PythonProcess("pandad", "selfdrive.boardd.pandad", offroad=True),
  PythonProcess("paramsd", "selfdrive.locationd.paramsd"),
  PythonProcess("plannerd", "selfdrive.controls.plannerd"),
  PythonProcess("radard", "selfdrive.controls.radard"),
  PythonProcess("thermald", "selfdrive.thermald.thermald", offroad=True),
  #PythonProcess("tombstoned", "selfdrive.tombstoned", enabled=not PC, offroad=True),
  #PythonProcess("updated", "selfdrive.updated", enabled=not PC, offroad=True),
  #PythonProcess("uploader", "selfdrive.loggerd.uploader", offroad=True),
  #PythonProcess("statsd", "selfdrive.statsd", offroad=True),
  #PythonProcess("gpxd", "selfdrive.gpxd.gpxd"),
  #PythonProcess("otisserv", "selfdrive.navd.otisserv", offroad=True),

  # EON only
  PythonProcess("rtshield", "selfdrive.rtshield", enabled=EON),
  PythonProcess("shutdownd", "selfdrive.hardware.eon.shutdownd", enabled=EON),
  PythonProcess("androidd", "selfdrive.hardware.eon.androidd", enabled=EON, offroad=True),

  # Experimental
  #PythonProcess("rawgpsd", "selfdrive.sensord.rawgps.rawgpsd", enabled=os.path.isfile("/persist/comma/use-quectel-rawgps")),
  NativeProcess("dmonitoringmodeld", "selfdrive/modeld", ["./dmonitoringmodeld"], enabled=dp_dm, callback=driverview),
  PythonProcess("dmonitoringd", "selfdrive.monitoring.dmonitoringd", enabled=dp_dm, callback=driverview),
  PythonProcess("dpmonitoringd", "selfdrive.dragonpilot.dpmonitoringd", enabled=not dp_dm),
  NativeProcess("sensord", "selfdrive/sensord", ["./sensord"], enabled=not PC, offroad=True, sigkill=EON),
  NativeProcess("ubloxd", "selfdrive/locationd", ["./ubloxd"], onroad=False, callback=ublox),
]

managed_processes = {p.name: p for p in procs}