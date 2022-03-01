import pyArango.connection as ADB
import blumycelium.mycelium as myc
import blumycelium.machine_elf as melf

from icecream import ic
import time

ic.configureOutput(includeContext=True)

class PrinterElf_demo3(melf.MachineElf):
    """docstring for Printer"""
    def task_print_it(self, to_print_lst) -> None:
        for to_print in to_print_lst:
            print(">>> Machine >>> Elf >>> Printer: '%s'" % to_print)

class SenderElf_demo3(melf.MachineElf):
    """docstring for Printer"""
    def task_send(self, to_send) -> ("value", ):
        return {
            "value": to_send
        }

def init_myc():
    users_to_create=[ {"username": "mycellium", "password": "mycellium"}]

    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    mycellium = myc.Mycellium(
        connection=connection,
        name="mycellium"
    )

    mycellium.init(init_db=True)
    mycellium.drop_jobs()
    
    printer = PrinterElf_demo3("The Elf Printer", mycellium) 
    printer.register(store_source=True)

    sender = SenderElf_demo3("The Elf Sender", mycellium)
    sender.register(store_source=True)
    
    msgs = ("a message sent on: %s" % time.ctime(), "a message sent on: %s" % time.ctime(), [ "mop", "kop", [ "hop", "clop"] ] )

    ret = sender.task_send( msgs )    
    # printer.task_print_it(ret["value"])

    # ret = sender.task_send( "Tralala"  )
    # printer.task_print_it( [ "hoplala", ret["value"], ret["value"], ret["value"] ] )

    sender.start_jobs(store_failures=True, raise_exceptions=True)
    print("===> print")
    printer.start_jobs(store_failures=True, raise_exceptions=True)

if __name__ == '__main__':
    init_myc()
