import pyArango.connection as ADB
import mycellium as myc
import machine_elf as melf

from icecream import ic
ic.configureOutput(includeContext=True)

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
    
    printer = PrinterElf("The Elf Printer", mycellium) 
    printer.register(store_source=True)
    # printer.task_print_it("lala")

    sender = SenderElf("The Sender Elf", mycellium)
    ret = sender.task_send("a message")
    
    # ic(ret)
    # ic(ret["value"])
    printer.task_print_it(ret["value"])

    sender.start_jobs(store_failures=False, raise_exceptions=True)
    printer.start_jobs(store_failures=False, raise_exceptions=True)

if __name__ == '__main__':
    init_myc()