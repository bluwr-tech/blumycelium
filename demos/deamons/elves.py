import blumycelium.machine_elf as melf


def load_json(json_filename):
    import json
    import time
    
    for nb in range(10):
        try:
            with open(json_filename) as fi:
                return json.load(fi)
        except Exception as exp:
            print("Unable to load file '%s' because of: '%s'"  % (json_filename, fi) )
    return None

class Animals(melf.MachineElf):
    """"""
    
    def set_animals(self, animal_list):
        self.animal_list = animal_list

    def task_get_animal_data(self) -> {"species": str, "weight": int}:
        import random

        name = random.choice(self.animal_list)
        
        return {
            "species": name,
            "weight": random.randint(0, 1000)
        }

class Storage(melf.MachineElf):
    """"""
    
    def set_database(self, json_filename):
        self.json_filename = json_filename

    def load_data(self):
        return load_json(self.json_filename)

    def task_save_animal_data(self, species:str, weight:int) -> None:
        import json

        database = self.load_data()
        
        if not database is None:
            if not species in database:
                database[species] = {"weight": [weight]}
            else:
                database[species]["weight"].append(weight)

            with open(self.json_filename, "w") as fi:
                print("Stored a new entry for:" + species)
                json.dump(database, fi)

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
        database = self.load_data()
        ret = {}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_mean(values["weight"])
        
        return {
            "means": ret
        }

    def task_calculate_mins(self) -> ["mins"]:
        database = self.load_data()
        ret = {}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_min(values["weight"])
        
        return {
            "mins": ret
        }

    def task_calculate_maxs(self) -> ["maxs"]:
        database = self.load_data()
        ret = {}
        if database:
            for name, values in database.items():
                ret[name] = self.calc_max(values["weight"])
        
        return {
            "maxs": ret
        }

class Formater(melf.MachineElf):
    """"""
    
    def task_print_stats(self, means, mins, maxs) -> None:
        for name in means:
            mean, min_value, max_value = means[name], mins[name], maxs[name]
            print("Stats for {name}:\n\tAverage: {mean}\n\tMinimum: {min}\n\tMaximum: {max}".format(name=name, mean=mean, min=min_value, max=max_value))

