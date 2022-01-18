from pyArango.collection import Collection, Edges, Field

import pyArango.validation as VAL
import bluwrserver.consts as consts
import bluwrserver.include.models.custom_validators as CVAL


class Results(Collection) :
    """results"""
    _fields = {
        "date": Field(validators=[VAL.NotNull()]),
        "data": Field(default=dict), # for storing stuff such as paths of generated files
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": True
    }

class Logs(Collection) :
    """"""
    _fields = {
        "date": Field(validators=[VAL.NotNull()]),
        "JobId": Field(validators=[VAL.NotNull()]),
        "taskId": Field(validators=[VAL.NotNull()]),
        "entityId": Field(validators=[VAL.NotNull()]),
        "resultId": Field(validators=[VAL.NotNull()]),
        "level": Field(validators=[VAL.Enumeration("debug", "info", "error", "warning")])
        "data": {
            "messaage": Field(validators=[VAL.NotNull()]),
            "traceback": Field(validators=[]),
            "more": Field(default=dict) #for more stuff
        }
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": True
    }

class Entities(Collection) :
    """Collection of all registered entities elves and bluwr"""
    _fields = {
        "date": Field(validators = [VAL.NotNull()]),
        "description": Field(validators = [VAL.NotNull()]),
        "type": Field(validators = [VAL.NotNull(), VAL.Enumeration(["bluwr", "elf"] )])
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Tasks(Collection) :
    """List of doable things"""
    _fields = {
        "date": Field(validators = [VAL.NotNull()]),
        "description": Field(validators = [VAL.NotNull()])
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Jobs(Collection) :
    """A task to be performed by an entity"""
    _fields = {
        "secondaryKeys": Field(default=dict), #for arbitrary markers such as user ids 
        "nextJobs": Field(default=list),
        "kwargs": Field(default=dict),
        "startDate": Field(validators = [VAL.NotNull()]),
        "endDate": Field(validators = [VAL.NotNull()]),
        "completed": Field(validators = [VAL.NotNull(), VAL.Bool()]),
        "startable": Field(validators = [VAL.NotNull(), VAL.Bool()]), # can the task be started i.e. has all the previous tasks finished
        "error": Field(validators = [VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }
