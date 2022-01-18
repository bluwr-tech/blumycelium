import time

class InitMycellium:
    """Initializes the mycellium"""
    def __init__(self):
        pass

    def init(self):
        pass

class Registrar:
    """register an entity or task"""
    def __init__(self, db):
        super(Registrar, self).__init__()
        self.db = db

    def register_entity(self, name, description, tasks_dict):
        now = time.time()
        myc_graph = db["Graphs"]["Mycellium"]

        entity = db["Entities"].createDocument()
        entity["_key"] = name
        entity["date"] = now
        entity["description"] = description
        entity.save()

        for task_def in tasks_dict:
            task = db["Tasks"].createDocument()
            entity["name"] = task_def["name"]
            entity["arguments"] = task_def["arguments"]
            entity["date"] = now
            entity["description"] = task_def["description"]
            
            myc_graph.link(entity, task, {"date": now})