import json
from loguru import logger
from panduza_platform import MetaDriver


class DriverSimpleFlasherOpenOCD(MetaDriver):

    ###########################################################################
    ###########################################################################

    def config(self):
        """ From MetaDriver
        """
        return {
            "compatible": "openocd_flasher",
            "info": { "type": "flasher", "version": "1.0" },
            "settings": { "openocd_mqtt_instance" : 'path to the openocd driver in the mqtt tree (ie : "pza/<machine name>/openocd/<driver name>")' }
        }

    ###########################################################################
    ###########################################################################

    def setup(self, tree):
        """ From MetaDriver
        """

        if "openocd_mqtt_instance" not in tree["settings"]:
            logger.error("openocd instance required")
        
        self.openocd_path = tree["settings"]["openocd_mqtt_instance"]

        self.register_command("flasher", self.__flash)
        pass

    ###########################################################################
    ###########################################################################

    def on_start(self):
        """ From MetaDriver
        """
        self.mqtt_client.subscribe(self.openocd_path + "/atts/#")
        self.mqtt_client.message_callback_add(self.openocd_path + "/atts/flasher", self.__resultCallback)
        pass

    ###########################################################################
    ###########################################################################


    def loop(self):
        """ From MetaDriver
        """
        return False


    #expected payload : { "addr" : <str>, "filename" : <str>, "bin": <str ascii (base64)> }
    def __flash(self, payload) :
        req = self.payload_to_dict(payload)
        # addr = req["addr"]
        # filename = req["filename"]
        # bin = req["bin"]
        self.mqtt_client.publish(self.openocd_path + "/cmds/flashWrite", payload)


    def __resultCallback(self, client, userdata, message):
        self.mqtt_client.publish(self.openocd_path + "/atts/result", message.payload)