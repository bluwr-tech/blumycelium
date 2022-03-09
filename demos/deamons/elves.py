import blumycelium.machine_elf as melf

#These elves connect to a fake database which is a json file
#This works as a design pattern that can be used to have
#elves work together on the same database
def load_json(json_filename, accept_empty=False):
    import json
    import time
    
    tries = 10
    nb = 0
    data = {}
    while nb < tries and len(data) < 1:
        try:
            with open(json_filename) as fi:
                data = json.load(fi)
        except Exception as exp:
            print("Unable to load file '%s' because of: '%s'"  % (json_filename, fi) )
        time.sleep(1)
        nb += 1
    return data

class Animals(melf.MachineElf):
    """"""
    
    def set_animals(self, animal_list):
        self.animal_list = animal_list

    def task_get_animal_data(self) -> {"species": str, "weight": int}:
        import random

        name = random.choice(self.animal_list)
        weight = random.randint(0, 1000)
        print(">new animal: %s, weight: %s" % (name, weight) )
        return {
            "species": name,
            "weight": weight
        }

class Storage(melf.MachineElf):
    """"""
    
    def set_database(self, json_filename):
        self.json_filename = json_filename

    def load_data(self):
        return load_json(self.json_filename)

    def task_save_animal_data(self, species:str, weight:int) -> None:
        import json
        import shutil

        database = self.load_data()
        
        if not database is None:
            if not species in database:
                database[species] = {"weight": [weight]}
            else:
                database[species]["weight"].append(weight)

            tmp_fn = self.json_filename + ".tmp"
            with open(tmp_fn , "w") as fi:
                json.dump(database, fi)
                print("Stored a new entry for:" + species)
            shutil.copyfile(tmp_fn, self.json_filename)

class Stats(melf.MachineElf):
    """"""
    
    def set_database(self, json_filename):
        self.json_filename = json_filename

    def load_data(self):
        return load_json(self.json_filename)

    def calc_mean(self, values):
        return sum(values)/len(values)

    def calc_max(self, values):
        return max(values)

    def calc_min(self, values):
        return min(values)

    def task_calculate_means(self) -> ["means"]:
        print(">calculating averages for all animals")
        database = self.load_data()
        ret ={}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_mean(values["weight"])
        
        return {
            "means": ret
        }

    def task_calculate_mins(self) -> ["mins"]:
        print(">finding min values for all animals")
        
        database = self.load_data()
        ret = {}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_min(values["weight"])
        
        return {
            "mins": ret
        }

    def task_calculate_maxs(self) -> ["maxs"]:
        print(">finding max values for all animals")
        
        database = self.load_data()
        ret ={}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_max(values["weight"])
        
        return {
            "maxs": ret
        }

class Formater(melf.MachineElf):
    """"""
    
    def task_print_stats(self, means, mins, maxs) -> None:
        print("====STATS====")
        for name in means:
            mean, min_value, max_value = means[name], mins[name], maxs[name]
            print("Stats for {name}:\n\tAverage: {mean}\n\tMinimum: {min}\n\tMaximum: {max}".format(name=name, mean=mean, min=min_value, max=max_value))
        print("=============")

