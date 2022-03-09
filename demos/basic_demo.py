import pyArango.connection as ADB
import blumycelium.mycelium as myc
import blumycelium.machine_elf as melf

import time

#This a very basic demo to show how BLUMUCELIUM
#is basically just python code. An Elf sends a message
#to another elf that prints it
#NOTICE THAT TASK ARE FUNCTION WITH NAMES STARING WITH 'task_'

class PrinterElf(melf.MachineElf):
    """docstring for Printer"""
    def task_print_it(self, to_print) -> None:
        print(">>> Machine >>> Elf >>> Printer: '%s'" % to_print)

class SenderElf(melf.MachineElf):
    """docstring for Printer"""
    def task_send(self, to_send) -> ("value", ):
        return {
            "value": to_send
        }

def init_myc():
    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    mycellium = myc.ArangoMycelium(
        connection=connection,
        name="mycellium"
    )

    mycellium.init(init_db=True)
    
    printer = PrinterElf("The Elf Printer", mycellium) 
    printer.register(store_source=True)

    sender = SenderElf("The Sender Elf", mycellium)
    sender.register(store_source=True)
    
    ret = sender.task_send("a message sent on: %s" % time.ctime())
    
    printer.task_print_it(ret["value"])

    sender.start_jobs(store_failures=True, raise_exceptions=True)
    print("===> print")
    printer.start_jobs(store_failures=True, raise_exceptions=True)

if __name__ == '__main__':
    init_myc()
