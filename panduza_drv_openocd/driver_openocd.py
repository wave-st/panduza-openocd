import time
import json
import os
import base64
from loguru import logger
from panduza_platform import MetaDriver
from openocd_python import *

class DriverOpenOCD(MetaDriver):
    ###########################################################################
    ###########################################################################

    def config(self):
        """ From MetaDriver
        """
        return {
            "compatible": "openocd",
            "info": { "type": "chip-debugger", "version": "1.0" },
            "settings": {
                "openocd_addr" : "openocd server address (optional)",
                "openocd_port" : "openocd telnet port (optional)",
                "target_polling" : "define if target state should be polled, at specified rate (optional)"
            }
        }

    ###########################################################################
    ###########################################################################

    def setup(self, tree):
        """ From MetaDriver
        """

        if "openocd_addr" not in tree["settings"]:
            logger.warning("openocd server address not specified, using default localhost")
            self.openocd_serv_addr = "localhost"
        else :
            self.openocd_serv_addr = tree["settings"]["openocd_addr"]
        

        if "openocd_port" not in tree["settings"]:
            self.openocd_serv_port = 6666
            logger.warning("openocd tcl rpc port not specified, using default " + str(self.openocd_serv_port))
        else :
            self.openocd_serv_port = tree["settings"]["openocd_port"]


        logger.info("openocd_serv_addr " + self.openocd_serv_addr)
        logger.info("openocd_serv_port " + str(self.openocd_serv_port))


        if "target_polling" not in tree["settings"] :
            self.state_polling = -1
            logger.info("target state polling not specified, disabled")
        else :
            self.state_polling = tree["settings"]["target_polling"]
            if(self.state_polling > 0) :
                logger.info("target state polling at " + str(self.state_polling) + "s")
            else :
                logger.info("target state polling disabled")

        self.openocd = OpenOCDClient(tcl_ip=self.openocd_serv_addr, tcl_port=self.openocd_serv_port).connect()

        self.register_command("getAvailableRegisters", self.__getAvailableRegisters)

        self.register_command("writeRegister", self.__writeRegister)
        self.register_command("writeMemory", self.__writeMemory)
       
        self.register_command("readRegister", self.__readRegister)
        self.register_command("readMemory", self.__readMemory)
        
        self.register_command("reset", self.__reset)
        self.register_command("halt", self.__halt)
        self.register_command("resetHalt", self.__resetHalt)
        self.register_command("getState", self.__getState)
        self.register_command("resume", self.__resume)

        self.register_command("flashWrite", self.__flashWrite)

        self.register_command("command", self.__openocdCommand)

        self.register_command("info", self.__getInfo)

        self.state = ""

        pass

    ###########################################################################
    ###########################################################################

    def on_start(self):
        """ From MetaDriver
        """
        self.__getState("")
        self.__getAvailableRegisters("")
        self.__getInfo("")
        # self.__showAll()

    ###########################################################################
    ###########################################################################

    def loop(self):
        """ From MetaDriver
        """
        if (self.state_polling > 0):
            self.__getState("")
            time.sleep(self.state_polling)
            return True
        return False

    def __showAll(self):
        self.__reset('')
        self.__halt('')
        self.__resetHalt('')
        self.__getState('')

        self.__getAvailableRegisters('')
        self.__writeRegister(bytes(json.dumps({ "reg" : "r0", "value" : "0x0" }), "utf-8"))
        self.__readRegister(bytes(json.dumps({ "reg" : "r0" }), "utf-8"))

        self.__writeMemory(bytes(json.dumps({ "addr" : "0x20000000", "value" : "0xbeef", "width" : 2 }), "utf-8"))
        self.__readMemory(bytes(json.dumps({ "addr" : "0x20000000", "width" : 8 }), "utf-8"))
        
        self.__resume('')

        self.__openocdCommand(bytes(json.dumps({ "cmd" : "echo $_TARGETNAME" }), "utf-8"))
        self.__getInfo('')

    def push_reg_names(self, value):
        self.push_attribute("target/cpu_registers", str(value), retain=True)


    def push_target_info(self, value, subtopic):
        self.push_attribute("target/" + str(subtopic), str(value), retain=True)


    def push_custom_command_result(self, cmd, result):
        payload_dict = {
            "cmd" : cmd,
            "result" : result
        }
        self.push_attribute("openocd_cmd/result" , json.dumps(payload_dict), retain=True)


    def push_memory_info(self, address, value, width):
        payload_dict = {
            "addr" : hex(address),
            "value" : hex(value),
            "width" : width
        }
        self.push_attribute("memory/map", json.dumps(payload_dict), retain=True)


    def push_flash_info(self, address, filename, result):
        payload_dict = {
            "addr" : hex(address),
            "filename" : filename,
            "size" : result,
            "complete" : (result > 0)
        }
        self.push_attribute("flash/map", json.dumps(payload_dict), retain=True)


    def push_reg_info(self, reg_name, value):
        payload_dict = {
            "addr" : reg_name,
            "value" : hex(value),
        }
        self.push_attribute("registers/map", json.dumps(payload_dict), retain=True)


    def __getInfo(self, payload):
        payload_dict = {
            "name" : self.openocd.getTargetName(),
            "endianness" : self.openocd.getEndianness(),
            "chipname" : self.openocd.getChipName(),
            "cputapid" : self.openocd.getCPUTAPID(),
            "workareasize" : self.openocd.getWorkAreaSize()
        }
        self.push_attribute("target/info", json.dumps(payload_dict), retain=True)


    def __readMemory(self, payload):
        """Memory read
            topic : <itf>/cmds/readMemory
            expected payload : { "addr" : <str>, "width" : <int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        # logger.info("readMemory")
        addr = int(req["addr"], 16)
        width = req["width"]
        try :
            value = self.openocd.readMemory(MemType(width * 8), addr)[addr]
            self.push_memory_info(addr, value, width)
        except :
            logger.error("read error")


    def __writeMemory(self, payload):
        """Memory write
            topic : <itf>/cmds/writeMemory
            expected payload : { "addr" : <str>, "value" : <str>, "width" : <int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        # logger.info("writeMemory")
        addr = int(req["addr"], 16)
        value = int(req["value"], 16)
        width = req["width"]
        try :
            self.openocd.writeMemory(MemType(width * 8), addr, value, check=False)
            read_value = self.openocd.readMemory(MemType(width * 8), addr)[addr]
            self.push_memory_info(addr, read_value, width)
        except :
            logger.error("write error")


    def __flashWrite(self, payload):
        """Flash binary file
            topic : <itf>/cmds/flashWrite
            expected payload : { "addr" : <str>, "filename" : <str>, "bin": <str ascii (base64)> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        addr = req["addr"]
        filename = req["filepath"]
        base64bin = req["bin"]
        bin = base64.b64decode(base64bin)
        path = ""
        
        if os.name == "posix" :
            path = "/tmp/"
        
        outputfile = open(path + filename, 'wb')
        outputfile.write(bin)
        outputfile.close()

        bytes_written = self.openocd.flashWrite(path + filename, addr)
        self.push_flash_info(addr, filename, bytes_written)


    def __readRegister(self, payload):
        """CPU Register read
            topic : <itf>/cmds/readRegister
            expected payload : { "reg" : <str/int> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        # logger.info("readRegister")
        reg_name = req["reg"]
        reg_val = self.openocd.readRegister(reg_name)
        self.push_reg_info(reg_name, reg_val)


    def __writeRegister(self, payload):
        """CPU Register write
            topic : <itf>/cmds/writeRegister
            expected payload : { "reg" : <str/int>, "value" : <str> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        # logger.info("writeRegister")
        reg_name = req["reg"]
        reg_val = req["value"]
        try :
            self.openocd.writeRegister(reg_name, reg_val)
            reg_val = self.openocd.readRegister(reg_name)
            self.push_reg_info(reg_name, reg_val)
        except :
            logger.error("write register error")


    def __getAvailableRegisters(self, payload):
        """CPU Register write
            topic : <itf>/cmds/writeRegister
            expected payload : { "reg" : <str/int>, "value" : <str> }
            note: additionnal fields are ignored
        """
        # logger.info("getAvailableRegisters")
        registers = self.openocd.getAvailableRegisters()
        res = dict()
        for register_name, width in registers.items() :
            res.update({ register_name : width.value })
        self.push_reg_names(res)
    

    def __reset(self, payload):
        """Trigger reset
            topic : <itf>/cmds/reset
            expected payload : {}
            note: additionnal fields are ignored
        """
        # logger.info("reset")
        self.__getState("")
        self.openocd.reset()
        self.__getState("")


    def __halt(self, payload):
        """Halt execution
            topic : <itf>/cmds/halt
            expected payload : {}
            note: additionnal fields are ignored
        """
        # logger.info("halt")
        self.__getState("")
        self.openocd.halt(blocking=True)
        self.__getState("")


    def __resetHalt(self, payload):
        """Reset then halt
            topic : <itf>/cmds/resetHalt
            expected payload : {}
            note: additionnal fields are ignored
        """
        self.__getState("")
        # logger.info("resetHalt")
        self.openocd.resetHalt(blocking=True)
        self.__getState("")


    def __getState(self, payload):
        """Trigger reset
            topic : <itf>/cmds/getState
            expected payload : {}
            note: additionnal fields are ignored
        """
        #logger.info("getState")
        self.state = self.openocd.getState().value
        self.push_target_info({ "value" : self.state }, "state")


    def __resume(self, payload):
        """Resume execution
            topic : <itf>/cmds/resume
            expected payload : {}
            note: additionnal fields are ignored
        """
        # logger.info("resume")
        self.openocd.resume()
        self.__getState("")


    def __openocdCommand(self, payload):
        """Send openOCD command
            topic : <itf>/cmds/resume
            expected payload : { "cmd" : <str> }
            note: additionnal fields are ignored
        """
        req = self.payload_to_dict(payload)
        cmd = req["cmd"]
        # logger.info("openocd command")
        result = self.openocd.command(cmd, verbose=True)
        self.push_custom_command_result(cmd, result)



    