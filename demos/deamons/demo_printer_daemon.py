import pyArango.connection as ADB
import mycellium as myc
import demo_elves as delf

from icecream import ic
import time

def run(duration):
    print("--launching printer")
    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    mycellium = myc.Mycellium(
        connection=connection,
        name="mycellium"
    )

    printer = delf.PrinterElf("The Printer Elf", mycellium)
    printer.register(store_source=True)

    now = time.time()
    stop_time = now + duration
    while time.time() < stop_time:
        printer.start_jobs(store_failures=True, raise_exceptions=True)
        time.sleep(1)

if __name__ == '__main__':
    run(60*1000*60*5)
