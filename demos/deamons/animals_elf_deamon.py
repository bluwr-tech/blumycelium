from async_orchestration import init_myc
from elves import Animals

def run(duration):
    import time

    mycellium = init_myc()

    #the name identify the elf uniquely
    #and must be the same as in orchestration file
    
    elf = Animals("animals creator", mycellium)
    elf.set_animals(["dolphin", "dog", "bee", "whale"])

    now = time.time()
    stop_time = now + duration
    while time.time() < stop_time:
        elf.start_jobs(store_failures=True, raise_exceptions=True)
        time.sleep(1)

if __name__ == '__main__':
    run(60*1000*60*5)
