from .driver_openocd import DriverOpenOCD
from .driver_memory import DriverMemoryOpenOCD
from .driver_reset import DriverResetOpenOCD
from .driver_flash import DriverSimpleFlasherOpenOCD

PZA_DRIVERS_LIST=[
    DriverOpenOCD,
    DriverMemoryOpenOCD,
    DriverResetOpenOCD,
    DriverSimpleFlasherOpenOCD
]