import pyArango.connection as ADB
import mycellium as myc

from icecream import ic

ic.configureOutput(includeContext=True)

def init_myc():
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

if __name__ == '__main__':
    init_myc()
