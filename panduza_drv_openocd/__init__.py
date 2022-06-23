from .driver_openocd import DriverOpenOCD
from .driver_memory import DriverMemoryOpenOCD
from .driver_reset import DriverResetOpenOCD

PZA_DRIVERS_LIST=[
    DriverOpenOCD,
    DriverMemoryOpenOCD,
    DriverResetOpenOCD
]