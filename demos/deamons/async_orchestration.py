def init_myc(drop=False):
    import pyArango.connection as ADB
    import blumycelium.mycelium as myc

    #Connect to the database.
    #It's not good practice to use root but this is just a demo, don't do it in prod. 
    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    #Instanciate the mycelium
    mycelium = myc.ArangoMycelium(
        connection=connection,
        name="animals_demo_mycelium"
    )

    if drop:
        #Drop all previous job information from the mycelium
        mycelium.drop()
    
    #Ensure the mycelium is initialized
    mycelium.init(init_db=True)

    return mycelium

def main():
    """
    The async demo is identical to the sync demo.
    The only difference being that start jobs a ran
    separate indiependent scripts
    """
   
    import elves
    import os
    import json
    import time

    if not os.path.exists("my_animals.json"):
        json_database_filename = "my_animals.json"
        with open(json_database_filename, "w") as fi:
            json.dump({}, fi)

    mycelium = init_myc(drop=True)

    #Ensure elves are registered in the mycelium
    animals = elves.Animals("animals creator", mycelium) 
    #True will save the source code of the elf in the mycelium
    #This has no effect on the way things run
    animals.register(store_source=True)

    store = elves.Storage("animals data store", mycelium) 
    store.register()
  
    #Here we create three instances of Stats. There's no need
    #to do it here because it is a sync example, however in async
    #this is what we would do to compute stats in parallel 
    mean_calc = elves.Stats("calc1", mycelium)
    mean_calc.register()
    
    min_calc = elves.Stats("calc2", mycelium)
    min_calc.register()
    
    max_calc = elves.Stats("calc3", mycelium)
    max_calc.register()
    
    printer = elves.Formater("report printer", mycelium)
    printer.register()

    #instanciating the jobs in the mycelium with 
    for nb in range(100):
        print("Sending: %s" % nb)
        mesurement = animals.task_get_animal_data()
        store.task_save_animal_data(species=mesurement["species"], weight=mesurement["weight"])
        #print stats every 10 iterations
        if nb % 5 ==0:
            mean = mean_calc.task_calculate_means()
            mins = min_calc.task_calculate_mins()
            maxs = max_calc.task_calculate_maxs()
            printer.task_print_stats(means=mean["means"], mins=mins["mins"], maxs=maxs["maxs"])
        time.sleep(1)
    
if __name__ == '__main__':
    main()
