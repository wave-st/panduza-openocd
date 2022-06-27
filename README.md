# panduza-openocd
Python panduza drivers for openocd

# Features
* driver_reset : trigger reset or reset halt
* driver_memory : read/write/poll memory

# Installing
`./install.sh`

# Panduza Tree config
This module forwards all of openocd-python to an mqtt interface.

```json
"interfaces": [
                {
		                "name": "openocd_interface",
                    "driver": "openocd",
                    "settings": {
                        "target_polling" : 0.5
                    }
                },
            	  {
                    "name": "reset_test",
                    "driver": "openocd_reset",
                    "settings": {
                    "openocd_mqtt_instance" : "pza/<machine name>/openocd/openocd_interface"
                    }
		            },
                {
                    "name": "memory_test",
                    "driver": "openocd_memory",
                    "settings": {
                    "openocd_mqtt_instance" : "pza/<machine name>/openocd/openocd_interface"
                    }
                }
            ]
```

# Requirements
[openocd-python module](https://github.com/wave-st/openocd-python)
