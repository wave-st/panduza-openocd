# panduza-openocd
Python panduza drivers for openocd

# Features
* openocd : mqtt bindings for openocd-python
* driver_reset : trigger reset or reset halt
* driver_memory : read/write/poll memory

# Installing
`./install.sh`

# Panduza Tree config
This module forwards all of openocd-python to an mqtt interface.
The mqtt path must be given to the drivers in order to communicate with the openocd interface.

```json
"interfaces": [
                {
		    "name": "openocd_interface",
                    "driver": "openocd",
                    "settings": {
		        "openocd_addr" : <openocd server address (optional, default "localhost")>
		        "openocd_port" : <openocd tcl rpc port (optional, default 6666)>
                        "target_polling" : <polling rate of target state in seconds (optional)>
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
