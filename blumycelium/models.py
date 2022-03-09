from pyArango.collection import Collection, Edges, Field
import pyArango.validation as VAL
import pyArango.graph as GR


COLLECTIONS = ["Jobs", "MachineElves", "MachineElvesRevisions", "Failures", "JobFailures", "Parameters", "JobParameters", "Results", "JobToJob"]
GRAPHS = ["Jobs_graph", "JobFailures_graph", "JobParameters_graph"]

class Jobs(Collection) :
    """Schema of a job in the database"""
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
        "parameter_ids": Field(default=list),
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
    """Schema of a failure in the database"""

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
    """Schema of a machine elf in the database"""

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
    """Schema of a machine elf revision in the database"""

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

class Parameters(Collection) :
    """Schema of a parameter in the database. A parameter is a variable passed as an argument to a task"""

    _fields = {
        "creation_date": Field(validators=[VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": True
    }

class Results(Collection) :
    """Schema of a result in the database"""

    _fields = {
        "creation_date": Field(validators=[VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": True
    }

class JobParameters(Edges) :
    """Schema of a job parameter in the database. a job parameter is an edge that associates a parameter to task argument"""

    _fields = {
        "creation_date": Field(validators=[VAL.NotNull()]),
        "name": Field(),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class JobToJob(Edges) :
    """Edge connecting jobs that depend on each other"""
    _fields = {
        "creation_date": Field(validators=[VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class JobParameters_graph(GR.Graph):
    """Graph connecting jobs to parameters"""
    _edgeDefinitions = (
        GR.EdgeDefinition("JobParameters", fromCollections = ["Jobs"], toCollections = ["Parameters"]),
    ) 
    _orphanedCollections = []

class JobFailures(Edges) :
    """Edge connecting jobs to failures"""
    _fields = {
        "creation_date" : Field(validators = [VAL.NotNull()])
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Jobs_graph(GR.Graph):
    """The job orchestration graph"""
    _edgeDefinitions = (
        GR.EdgeDefinition("JobToJob", fromCollections = ["Jobs"], toCollections = ["Jobs"]),
    ) 
    _orphanedCollections = []

class JobFailures_graph(GR.Graph):
    """Graph connecting jobs to failures"""
    _edgeDefinitions = (
        GR.EdgeDefinition("JobFailures", fromCollections = ["Jobs"], toCollections = ["Failures"]),
    ) 
    _orphanedCollections = []

