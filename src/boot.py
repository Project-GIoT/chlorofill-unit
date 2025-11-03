import gc
import esp
import os
import sys
import machine

import config

esp.osdebug(None)
gc.enable()
gc.collect()

RESET_CAUSES = {
    machine.PWRON_RESET: "Power-On Reset",
    machine.HARD_RESET: "Hardware Reset",
    machine.WDT_RESET: "Watchdog Reset",
    machine.DEEPSLEEP_RESET: "Deep Sleep Wake",
    machine.SOFT_RESET: "Soft Reset",
}

WAKE_REASONS = {
    getattr(machine, "PIN_WAKE", None): "External Pin",
    getattr(machine, "RTC_WAKE", None): "Real-Time Clock",
    getattr(machine, "TIMER_WAKE", None): "Timer",
    getattr(machine, "TOUCHPAD_WAKE", None): "Touchpad",
    getattr(machine, "ULP_WAKE", None): "Ultra Low Power",
    None: "Unknown",
}

def boot_banner():
    print("\n\n")
    # print(" ██████╗██╗  ██╗██╗      ██████╗ ██████╗  ██████╗ ███████╗██╗██╗     ██╗     ")
    # print("██╔════╝██║  ██║██║     ██╔═══██╗██╔══██╗██╔═══██╗██╔════╝██║██║     ██║     ")
    # print("██║     ███████║██║     ██║   ██║██████╔╝██║   ██║█████╗  ██║██║     ██║     ")
    # print("██║     ██╔══██║██║     ██║   ██║██╔══██╗██║   ██║██╔══╝  ██║██║     ██║     ")
    # print("╚██████╗██║  ██║███████╗╚██████╔╝██║  ██║╚██████╔╝██║     ██║███████╗███████╗")
    # print(" ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝")
    print("==========================================================================")
    print("                            ChloroFill System Booting                     ")
    print("==========================================================================")
    print(" Created by : Ernest Louis S. Villacorta")
    print(" Note       : Developed as part of a high school research thesis project,")
    print("                 with technical mentorship and guidance provided by me.")
    print("--------------------------------------------------------------------------")

    print(f" Firmware : {sys.version.split(' ')[0]} ({sys.platform})")
    print(f" Memory   : {gc.mem_free()} bytes free")

    try:
        stats = os.statvfs('/')
        total = stats[0] * stats[2]
        free = stats[0] * stats[3]
        used = total - free
        print(f" Storage  : {used//1024} KB used / {total//1024} KB total")
    except:
        print(" Storage  : unavailable")

    reset_cause = RESET_CAUSES.get(machine.reset_cause(), f"Unknown ({machine.reset_cause()})")
    wake_reason = WAKE_REASONS.get(machine.wake_reason(), f"Unknown ({machine.wake_reason()})")

    print(f" Reset    : {reset_cause}")
    print(f" Wake     : {wake_reason}")
    print("--------------------------------------------------------------------------")
    print(" Environment ready — photosynthesizing...")
    print("\n")

if not config.DEBUG:
    boot_banner = lambda: None

boot_banner()

