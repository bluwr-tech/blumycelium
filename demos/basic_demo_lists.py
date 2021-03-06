import pyArango.connection as ADB
import blumycelium.mycelium as myc
import blumycelium.machine_elf as melf

import time

#This a very basic demo to show how BLUMUCELIUM
#is basically just python code. An Elf sends a message
#to another elf that prints it
#In this slightly more complicated example, we manipulate lists
#in various ways. Like we would normally do in python
##NOTICE THAT TASK ARE FUNCTION WITH NAMES STARING WITH 'task_'

class PrinterElf_demo3(melf.MachineElf):
    """docstring for Printer"""
    def task_print_it(self, to_print_lst) -> None:
        # ic(to_print_lst)
        for to_print in to_print_lst:
            print(">>> Machine >>> Elf >>> Printer: '%s'" % to_print)

class SenderElf_demo3(melf.MachineElf):
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

    mycelium = myc.ArangoMycelium(
        connection=connection,
        name="mycelium"
    )

    mycelium.init(init_db=True)
    mycelium.drop_jobs()
    
    printer = PrinterElf_demo3("The Elf Printer", mycelium) 
    printer.register(store_source=True)

    printer2 = PrinterElf_demo3("The Elf Printer2", mycelium) 
    printer2.register(store_source=True)

    sender = SenderElf_demo3("The Elf Sender", mycelium)
    sender.register(store_source=True)
    
    msgs = ("a message sent on: %s" % time.ctime(), "a message sent on: %s" % time.ctime(), [ "mop", "kop", [ "hop", "clop"] ] )
    ret = sender.task_send( msgs )
    printer.task_print_it(ret["value"])

    ret = sender.task_send( "Tralala"  )
    printer.task_print_it( [ [ ret["value"] ] * 10, [ ret["value"], [ret["value"]]] ] )
    printer2.task_print_it( [ ret["value"].upper(), [ ret["value"]*2, [ret["value"], "TRA"]] ] )

    sender.start_jobs(store_failures=True, raise_exceptions=True)
    printer.start_jobs(store_failures=True, raise_exceptions=True)
    printer2.start_jobs(store_failures=True, raise_exceptions=True)

if __name__ == '__main__':
    init_myc()
