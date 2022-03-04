from . import utils as ut
from . import custom_types
from . import graph_parameters as gp

from icecream import ic

class ValuePlaceholder(gp.Value):

    def _init(self, run_job_id, name, *args, **kwargs):
        super(ValuePlaceholder, self)._init(*args, **kwargs)
        self.run_job_id = run_job_id
        self.name = name
        self.result_id = self.get_result_id(self.run_job_id, self.name)

        self.parameter.set_origin(self.result_id)

    @classmethod
    def get_result_id(cls, job_id, name):
        return ut.legalize_key(job_id + name)

class TaskReturnPlaceHolder:
    """docstring for TaskReturnPlaceHolder"""
    def __init__(self, worker_elf, task_function, run_job_id):
        self.task_function = task_function
        self.worker_elf = worker_elf
        self.run_job_id = run_job_id
        self.parameters = {}
        self.is_none = False
        
    def make_placeholder(self):
        from inspect import signature, _empty

        sig = signature(self.task_function)
        ret_annotation = sig.return_annotation

        self.is_none = False
        if (ret_annotation is _empty) :
            raise Exception("Task return annotation cannot be empty, expecting None, tuple or list of parameter keys. Got: '%s'" % ret_annotation)
        
        if (ret_annotation is None) :
            self.is_none = True
        elif (type(ret_annotation) not in [list, tuple]) :
            raise Exception("Task return annotation cannot be empty, expecting None, tuple or list of parameter keys. Got: '%s'" % ret_annotation)

        if not self.is_none:
            if type(ret_annotation) is dict:
                for name, value in ret_annotation.items():
                    self.parameters[name] = ValuePlaceholder(self.run_job_id, name, as_type=value)
            else:
                for name in ret_annotation:
                    self.parameters[name] = ValuePlaceholder(self.run_job_id, name)
            
    def get_result_id(self, name):
        if name not in self.parameters:
            raise Exception("Placeholder has no parameter: '%s'" % name)

        return self.parameters[name].result_id
        # return ValuePlaceholder.get_result_id(self.run_job_id, name)

    def __getitem__(self, key):
        if self.is_none:
            return None
        # ic(key, type(self.parameters[key]), self.parameters[key])
        return self.parameters[key]

    def __str__(self):
        if self.is_none:
            return "*-%s: None-*"% self.__class__.__name__

        return "*-%s: %s-*" %( self.__class__.__name__, str(self.parameters) )

    def __repr__(self):
        return str(self)

class TaskParameters:

    def __init__(self, fct, run_job_id):
        from inspect import signature

        self.run_job_id = run_job_id
        self.signature = signature(fct)
        self.final_args = {}

    def set_parameters(self, *args, **kwargs):
        from inspect import _empty

        ret_annotation = self.signature.return_annotation
        parameters = self.signature.parameters
        self.final_args = {}
        
        for pid, param in enumerate(parameters):
            if pid < len(args):
                self.final_args[param] = args[pid]
            elif param in kwargs:
                if param in self.final_args:
                    raise Exception("Got 2 values for parameter '{param}', ( {val1} & {val2})".format(param, self.final_args[param], kwargs[param]))
                self.final_args[param] = kwargs[param]
            else:
                if parameters[param].default is _empty:
                    raise Exception("Mandatory parameter '{param}' missing)".format(param=param))
                self.final_args[param] = parameters[param].default
                
        return self.final_args
    
    def find_placeholders_in_key_value_iterrator(self, iterator):
        """find placeholders in dicts lists etc..."""
        placeholders = {}
        for key, value in iterator:
            if isinstance(value, ValuePlaceholder):
                placeholders[str(key)] = value
        return placeholders

    def validate(self):
        from inspect import _empty

        accepted_types = [dict, list, tuple, int, float, bool]

        parameters = self.signature.parameters
        for param, value in self.final_args.items():
            if not isinstance(value, ValuePlaceholder):
                param_clas = None
                if not parameters[param].annotation is _empty :
                    param_clas = parameters[param].annotation
                elif not parameters[param].default is _empty :
                    param_clas = type(parameters[param].default)

                if not (param_clas is type(None)) and param_clas and not isinstance(value, param_clas):
                    raise Exception("Param '{param}' has the wrong type {type} expected {exp})".format(param=param, type=type(value), exp=param_clas))

                if param_clas and (not param_clas in accepted_types ) :
                    raise Exception("Param '{param}' has the wrong type {type} expected one of the following: {exp})".format(param=param, type=type(value), exp=accepted_types))

        return True

    def get_storable_type(self, obj):
        """
        get a type storable by the mycellum for obj
            [list, tuple] -> array
            dict -> obj
            [str, float, int] -> primitive
            None -> null
        """
        if type(obj) in [list, tuple]:
            return "array"
        elif type(obj) is dict:
            return "object"
        elif type(obj) in [str, float, int]:
            return "primitive"
        elif type(obj) in type(None):
            return "null"
        else:
            raise Exception("Unknown type; %s must be in %s" % (type(obj), [list, tuple, dict, str, float, int]))

    def get_parameter_dict(self):
        params = {}
        for name, arg in self.final_args.items():
            # ic(name, arg)
            if type(arg) in [dict, list, tuple, set]:
                param = gp.unravel(arg)
                val = ValuePlaceholder(self.run_job_id, name)
                val.parameter = param
            elif not isinstance(arg, ValuePlaceholder):
                # print("=================================")
                # ic(arg)
                val = ValuePlaceholder(self.run_job_id, name)
                val.set_value(arg)
            else:
                val = arg
            params[name] = val.traverse(to_dict=True)
        return params

    @classmethod
    def develop(cls, dct_params:dict):
        ret = {}
        for key, trav in dct_params.items():
            ret[key] = gp.GraphParameter.build_from_traversal(trav)
            # ic(key, ret[key])
            # ic(ret[key].make())
            ret[key] = ret[key].make()
        return ret

class Job:
    """docstring for Job"""
    def __init__(
        self,
        task,
        run_job_id,
        worker_elf,
        parameters,
        submit_date,
        start_date,
        completion_date,
        status,
        mycelium,
        return_placeholder
    ):
        self.task=task
        self.run_job_id=run_job_id
        self.worker_elf=worker_elf
        self.parameters=parameters
        self.submit_date=submit_date
        self.start_date=start_date
        self.completion_date=completion_date
        self.status=status
        self.mycelium = mycelium
        self.return_placeholder=return_placeholder

    def commit(self):
        self.mycelium.push_job(self)

class Task:
    """docstring for Task"""
    def __init__(self, machine_elf, function, name):
        self.machine_elf = machine_elf
        self.function = function
        self.name = name
        # self.parameters = None
        self.return_placeholder = None

        self.source_code = None
        self.revision = None
        self.documentation = None
        self.signature = None
        
        self.inspect_function()

    def inspect_function(self):
        import hashlib

        self.source_code = ut.inpsect_none_if_exception_or_empty(self.function, "getsource")
        self.revision = ut.legalize_key(self.name + ut.get_hash_key(self.source_code))
        self.documentation = ut.inpsect_none_if_exception_or_empty(self.function, "cleandoc")
        self.signature = ut.inpsect_none_if_exception_or_empty(self.function, "signature")

    def wrap(self, *args, **kwargs):
        args = args
        kwargs = kwargs
        run_job_id = ut.getuid()

        def _wrapped():
            parameters = TaskParameters(self.function, run_job_id=run_job_id)
            parameters.set_parameters(*args, **kwargs)
            parameters.validate()

            now = ut.gettime()
            
            return_placeholder = TaskReturnPlaceHolder(worker_elf=self.machine_elf.uid, task_function=self.function, run_job_id=run_job_id)
            return_placeholder.make_placeholder()

            job = Job(
                task = self,
                run_job_id = run_job_id,
                worker_elf = self.machine_elf,
                parameters = parameters,
                submit_date = now,
                start_date = None,
                completion_date = None,
                status = custom_types.STATUS["PENDING"],
                mycelium = self.machine_elf.mycelium,
                return_placeholder=return_placeholder
            )
            
            job_id = job.commit()

            return return_placeholder

        return _wrapped

    # def run(self, *args, **kwargs):
    #     return self.function(*args, **kwargs)

    def run(self, job_id, *args, **kwargs):
        fct_ret = self.function(*args, **kwargs)
        
        ret = {}
        for name, value_ret in fct_ret.items():
            ret[name] = {
                "result_id": ValuePlaceholder.get_result_id(job_id, name),
                "value": value_ret
            }

        return ret

    def __call__(self, *args, **kwargs):
        return self.wrap( *args, **kwargs )()

    def __str__(self):
        return "*-Task '%s.%s': %s -*" % (self.machine_elf.uid, self.name, self.signature)

    def __repr__(self):
        return str(self)

class MachineElf:
    """docstring for MachineElf"""

    def __init__(self, uid, mycelium):
        self.uid = ut.legalize_key(uid)
        self.mycelium = mycelium
        self.tasks = {}

        self.source_code = None
        self.revision = None
        self.documentation= None
        
        self.inspect_self()
        self.find_tasks()

    def inspect_self(self): 
        self.source_code = ut.inpsect_none_if_exception_or_empty(self.__class__, "getsource")
        self.revision = ut.get_hash_key(self.source_code+self.uid, prefix=self.__class__.__name__ )
        self.documentation = ut.inpsect_none_if_exception_or_empty(self.__class__, "cleandoc")

    def find_tasks(self):
        import inspect

        for name, member in inspect.getmembers(self):
            if name.startswith("task_") and inspect.ismethod(member):
                task = Task(self, member, name)
                self.tasks[name] = task
                setattr(self, name, task)

    def register(self, store_source):
        self.mycelium.register_machine_elf(self, store_source)

    def get_jobs(self):
        return self.mycelium.get_jobs(self.uid)

    # def is_job_ready(self, parameters:dict, embedded_params:dict):
    #     import custom_types
    #     params_ready = not (custom_types.EmptyParameter in parameters.values() )
        
    #     for key, value in embedded_params.items():
    #         if value is custom_types.EmptyParameter:
    #             return False
        
    #     return params_ready

    def start_jobs(self, store_failures=True, raise_exceptions=True):
        jobs = self.mycelium.get_received_jobs(self.uid)
        for job in jobs:
            params = self.mycelium.get_job_parameters(job["id"])
            params = TaskParameters.develop(params)

            if job["status"] == custom_types.STATUS["PENDING"] :
                self.run_task(job["id"], job["task"]["name"], params, store_failures=store_failures, raise_exceptions=raise_exceptions)

    # def start_jobs(self, store_failures=True, raise_exceptions=True):
    #     jobs = self.mycelium.get_received_jobs(self.uid)
    #     for job in jobs:
    #         params = self.mycelium.get_job_parameters(job["id"], embedded=False)
    #         params.update( self.mycelium.get_job_static_parameters(job["id"]) )
    #         embedded_params = self.mycelium.get_job_parameters(job["id"], embedded=True)
            
    #         for emb_value in embedded_params.values():
    #             value = emb_value["value"]
    #             emb = emb_value["embedding"]
    #             parent_obj = params[ emb["parent_parameter_name"] ]
    #             insert_fct = getattr(parent_obj, emb["embedding_function"])
    #             insert_fct( int(emb["self_name"]), value)

    #         if job["status"]!= custom_types.STATUS["DONE"] and self.is_job_ready(params, embedded_params):
    #             self.run_task(job["id"], job["task"]["name"], params, store_failures=store_failures, raise_exceptions=raise_exceptions)

    def run_task(self, job_id:str, task_name:str, parameters:dict, store_failures:bool, raise_exceptions:bool):
        import sys
        try:
            task = getattr(self, task_name)
            self.mycelium.start_job(job_id)
            ret = task.run(job_id, **parameters)
            ic(ret)
            self.mycelium.store_results(job_id, ret)
            # self.mycelium.update_job_status(job_id, custom_types.STATUS["DONE"])
            self.mycelium.complete_job(job_id)
        except Exception as exp:
            if store_failures:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.mycelium.register_job_failure(exc_type, exc_value, exc_traceback, job_id)
            
            if raise_exceptions:
                raise exp

        return ret
