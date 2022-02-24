import pyArango.connection as ADB
import mycellium as myc

import demo_elves as delf

from icecream import ic
import time

def run(nb_messages):
    print("---lanching logic")

    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    mycellium = myc.Mycellium(
        connection=connection,
        name="mycellium"
    )

    sender = delf.SenderElf("The Sender Elf", mycellium)
    printer = delf.PrinterElf("The Printer Elf", mycellium) 

    for _ in range(nb_messages):
        msg = "a message sent on: %s" % time.ctime()
        print("sending message: %s" % msg)
  
        ret = sender.task_send(msg)

        printer.task_print_it(ret["value"], suffix="hoplala")

        time.sleep(1)

if __name__ == '__main__':
    run(100)
