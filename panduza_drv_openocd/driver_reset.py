from loguru import logger
from panduza_platform import MetaDriver
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish

# pza/alim_test/reset_openocd/reset_test/atts/state
# {"haltAfterReset": false}

class DriverResetOpenOCD(MetaDriver):

    ###########################################################################
    ###########################################################################

    def config(self):
        """ From MetaDriver
        """
        return {
            "compatible": "openocd_reset",
            "info": { "type": "reset", "version": "1.0" },
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

        self.register_command("reset/trigger", self.__trigger_reset)

        pass

    ###########################################################################
    ###########################################################################

    def on_start(self):
        """ From MetaDriver
        """
        # subscribe.callback(self.__trackState, self.openocd_path + "/atts/target/state", hostname=self.broker.addr)
        self.mqtt_client.subscribe(self.openocd_path + "/atts/#")
        self.mqtt_client.message_callback_add(self.openocd_path + "/atts/target/state", self.__trackState)

    ###########################################################################
    ###########################################################################

    def loop(self):
        """ From MetaDriver
        """
        return False


    def __trackState(self, client, userdata, message):
        self.push_attribute("state", message.payload)


    def __trigger_reset(self, payload):
        """Trigger Reset
            topic : <itf>/cmds/reset/trigger
            expected payload : { "haltAfterReset" : <bool> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        logger.info("reset triggered!")

        if (req["haltAfterReset"]) :
            self.mqtt_client.publish(self.openocd_path + "/cmds/resetHalt", "{}", hostname=self.broker.addr)
        else :
            self.mqtt_client.publish(self.openocd_path + "/cmds/reset", "{}", hostname=self.broker.addr)





