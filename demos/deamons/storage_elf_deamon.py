from async_orchestration import init_myc
from elves import Storage

def run(duration):
    import time

    mycellium = init_myc()

    #the name identify the elf uniquely
    #and must be the same as in orchestration file    
    elf = Storage("animals data store", mycellium)
    elf.set_database("my_animals.json")
    
    now = time.time()
    stop_time = now + duration
    while time.time() < stop_time:
        elf.start_jobs(store_failures=True, raise_exceptions=True)
        time.sleep(1)

if __name__ == '__main__':
    run(duration=60*1000*60*5)
