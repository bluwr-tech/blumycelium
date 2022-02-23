from pyArango.collection import Collection, Edges, Field
import pyArango.validation as VAL
import pyArango.graph as GR


COLLECTIONS = ["Jobs", "MachineElves", "MachineElvesRevisions", "Results"]
GRAPHS = ["Jobs_graph"]

class Jobs(Collection) :
    _fields = {
        "id" : Field(), #placeholder to be able to use ["id"]
        "task" : {
            "name": Field(validators = [VAL.NotNull()]),
            "signature": Field(validators = [VAL.NotNull()]),
            "source_code": Field(),
            "documentation": Field(),
            "revision": Field(),
        },
        "machine_elf" : {
            "id": Field(validators = [VAL.NotNull()]),
            "documentation": Field(),
            "revision": Field(),
        },
        "static_parameters": Field(default=dict),
        "submit_date" : Field(validators = [VAL.NotNull()]),
        "start_date": Field(),
        "completion_date": Field(),
        "status": Field(validators = [VAL.NotNull()]),
        
        "error_type": Field(),
        "error_traceback": Field(),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class MachineElves(Collection) :
    _fields = {
        "documentation": Field(),
        "last_revision": Field(),
        "creation_date" : Field(validators = [VAL.NotNull()]),
        "revisions": {
            "dates": Field(default=list),
            "hashes": Field(default=list),
        }
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class MachineElvesRevisions(Collection) :
    _fields = {
        "documentation": Field(),
        "creation_date" : Field(validators = [VAL.NotNull()]),
        "source_code": Field()
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Results(Collection) :
    _fields = {
        "value": Field(),
        "creation_date" : Field(validators = [VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Parameters(Edges) :
    _fields = {
        "submit_date" : Field(validators = [VAL.NotNull()]),
        "value_id" : Field(),
        "completion_date": Field(),
        "status": Field(validators = [VAL.NotNull()])
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Jobs_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("Parameters", fromCollections = ["Jobs"], toCollections = ["Jobs"]),
    ) 
    _orphanedCollections = []


# class Results_graph(GR.Graph):
#     _edgeDefinitions = (
#         GR.EdgeDefinition("Results", fromCollections = ["MachineElves"], toCollections = ["MachineElves"]),
#     ) 
#     _orphanedCollections = []
