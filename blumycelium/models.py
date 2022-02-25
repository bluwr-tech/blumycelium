from pyArango.collection import Collection, Edges, Field
import pyArango.validation as VAL
import pyArango.graph as GR


COLLECTIONS = ["Jobs", "MachineElves", "MachineElvesRevisions", "Results", "Failures", "Parameters", "JobFailures"]
GRAPHS = ["Jobs_graph", "JobFailures_graph"]

class Jobs(Collection) :
    _fields = {
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
        "end_date": Field(),
        "status": Field(validators = [VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Failures(Collection) :
    _fields = {
        "type": Field(validators = [VAL.NotNull()]),
        "value": Field(validators = [VAL.NotNull()]),
        "traceback": Field(validators = [VAL.NotNull()]),
        "creation_date": Field(validators = [VAL.NotNull()])
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
        "name": Field(validators = [VAL.NotNull()]),
        "submit_date" : Field(validators = [VAL.NotNull()]),
        "result_id" : Field(validators = [VAL.NotNull()]),
        "completion_date": Field(),
        "status": Field(validators = [VAL.NotNull()]),
        "value": Field(),
        "static": Field(default=False),
        "embedded": Field(default=False),
        # "embedding":{
        #     "parent_parameter_name": Field(),
        #     "self_name": Field(),
        #     "embedding_function": Field()
        # }
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class ParameterOperations(Edges) :
    _fields = {
        "function_name": Field()
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class JobFailures(Edges) :
    _fields = {
        "creation_date" : Field(validators = [VAL.NotNull()])
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


class JobFailures_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("JobFailures", fromCollections = ["Jobs"], toCollections = ["Failures"]),
    ) 
    _orphanedCollections = []

class ParameterOperations_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("ParameterOperations", fromCollections = ["Parameters"], toCollections = ["Parameters"]),
    ) 
    _orphanedCollections = []

