import time
import json
from loguru import logger
from panduza_platform import MetaDriver
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish


class DriverMemoryOpenOCD(MetaDriver):

    ###########################################################################
    ###########################################################################

    def config(self):
        """ From MetaDriver
        """
        return {
            "compatible": "openocd_memory",
            "info": { "type": "memory", "version": "1.0" },
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

        self.register_command("read", self.__read)
        self.register_command("write", self.__write)
        self.register_command("watch", self.__watch)
        self.map = dict()
        self.map.update({"regs" : []})
        self.authlist = set()
        self.watchlist = dict()
        self.millis = int(round(time.time() * 1000))
        # self.loop()
        pass

    ###########################################################################
    ###########################################################################

    def on_start(self):
        """ From MetaDriver
        """
        # subscribe.callback(self.__trackRead, self.openocd_path + "/atts/memory/map", hostname=self.broker.addr)
        self.mqtt_client.subscribe(self.openocd_path + "/atts/#")
        self.mqtt_client.message_callback_add(self.openocd_path + "/atts/memory/map", self.__trackRead)
        pass

    ###########################################################################
    ###########################################################################

    def loop(self):
        """ From MetaDriver
        """
        current_millis = int(round(time.time() * 1000))
        time_passed = current_millis - self.millis

        for el in self.watchlist.items() :
            addr = el[0]
            if (self.watchlist[addr]["timer"] <= 0) :
                self.authlist.add(addr)
                self.__poll(addr, self.watchlist[addr]["width"])
                self.watchlist[addr]["timer"] = self.watchlist[addr]["pollTime"]
            else :
                self.watchlist[addr]["timer"] -= time_passed
                # logger.info('self.watchlist[addr]["timer"]: ' + str(self.watchlist[addr]["timer"]))

        self.millis = current_millis
        time.sleep(0.001)
        return True


    def __pushMap(self) :
        self.push_attribute("map", json.dumps(self.map), retain=True)


    def __updateMap(self, entry):
        if(entry["addr"] not in self.authlist):
            return
        
        found = False
        for el in self.map["regs"]:
            if(el["addr"] == entry["addr"]) :
                self.map["regs"].remove(el)
                self.map["regs"].append(entry)
                found = True
                logger.info("updated entry addr " + entry["addr"])
        
        if not found :
            self.map["regs"].append(entry)
            logger.info("created new entry for addr " + entry["addr"])

        self.authlist.remove(entry["addr"])

        self.__pushMap()


    def __trackRead(self, client, userdata, message):
        self.__updateMap(self.payload_to_dict(message.payload))


    def __poll(self, addr, width) :
        payload = {
            "addr" : addr,
            "width" : width
        }
        self.authlist.add(addr.lower())
        self.mqtt_client.publish(self.openocd_path + "/cmds/readMemory", json.dumps(payload))



    def __read(self, payload):
        """Read from memory
            topic : <itf>/cmds/read
            expected payload : { "addr" : <str>, "width" : <int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        self.authlist.add(req["addr"].lower())
        self.mqtt_client.publish(self.openocd_path + "/cmds/readMemory", json.dumps(req))



    def __write(self, payload):
        """Write to memory
            topic : <itf>/cmds/write
            expected payload : { "addr" : <str>, "value" : <str>, "width" : <int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        self.authlist.add(req["addr"].lower())
        self.mqtt_client.publish(self.openocd_path + "/cmds/writeMemory", payload)


    def __watch(self, payload):
        """Memory polling
            topic : <itf>/cmds/watch
            expected payload : { "addr" : <str>, "pollTime": <int>, "width" : <int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        addr = req["addr"].lower()
        width = req["width"]
        pollTime = req["pollTime"]
        if(pollTime > 0):
            self.watchlist.update({ addr : { "width" : width, "pollTime" : pollTime, "timer" : pollTime } })
            logger.info("enabled watch for addr " + addr)
        else :
            del self.watchlist[addr]
            logger.info("disabled watch for addr " + addr)