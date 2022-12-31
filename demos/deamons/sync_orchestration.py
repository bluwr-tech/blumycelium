def init_myc():
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

    #Ensure the mycelium is initialized
    mycelium.init(init_db=True)

    #Drop all previous job information from the mycelium
    mycelium.drop()

    return mycelium

def main():
    import elves
    import os
    import json

    #Elves in this demo will have to connect to an external database (containing metrics about some animals) and compute stats
    #This database is represented here by a simple json file.
    #All information about job executions and dependencies are stored in the mycelium (Arangodb)
    json_database_filename = "my_animals.json"
    with open(json_database_filename, "w") as fi:
        json.dump({}, fi)

    mycelium = init_myc()

    #Ensure elves are registered in the mycelium
    #This one will simply return random values for some animals
    animals = elves.Animals(
        uid="animals creator", 
        mycelium=mycelium
    ) 
    #True will save the source code of the elf in the mycelium
    #This has no effect on the way things run
    animals.register(store_source=True)
    animals.set_animals(["dolphin", "dog", "bee", "whale"])

    #This second elf will store the values sent from the first one in the database (simple json file here)
    store = elves.Storage("animals data store", mycelium) 
    store.register()
    store.set_database(json_database_filename)

    #Here we create three instances of Stats. There's no need
    #to do it here because it is a sync example, however in async
    #this is what we would do to compute stats in parallel 
    mean_calc = elves.Stats("average calculator", mycelium)
    mean_calc.register()
    mean_calc.set_database(json_database_filename)
    
    min_calc = elves.Stats("min calculator", mycelium)
    min_calc.register()
    min_calc.set_database(json_database_filename)
    
    max_calc = elves.Stats("max calculator", mycelium)
    max_calc.register()
    max_calc.set_database(json_database_filename)
    
    printer = elves.Formater("report printer", mycelium)
    printer.register()

    #instanciating the jobs in the mycelium with 
    #The following describes how the code should be run but it is not exactly this code that will be executed
    #The execution DAG will be stored in the mycelium and executed when necessary
    for nb in range(10):
        mesurement = animals.task_get_animal_data()
        store.task_save_animal_data(species=mesurement["species"], weight=mesurement["weight"])
        mean = mean_calc.task_calculate_means()
        mins = min_calc.task_calculate_mins()
        maxs = max_calc.task_calculate_maxs()
        printer.task_print_stats(means=mean["means"], mins=mins["mins"], maxs=maxs["maxs"])

    #start jobs store_failures will ensure that any exception will be
    #stored in the mycelium. raise_exceptions will cause the excepption
    #to not be bypassed
    animals.start_jobs(store_failures=True, raise_exceptions=True)
    store.start_jobs(store_failures=True, raise_exceptions=True)
    mean_calc.start_jobs(store_failures=True, raise_exceptions=True)
    min_calc.start_jobs(store_failures=True, raise_exceptions=True)
    max_calc.start_jobs(store_failures=True, raise_exceptions=True)
    printer.start_jobs(store_failures=True, raise_exceptions=True)

if __name__ == '__main__':
    main()