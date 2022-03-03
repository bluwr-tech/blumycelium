from . import utils as ut
from . import custom_types
from . import graph_parameters as gp

from icecream import ic

class ValuePlaceholder(gp.Value):

    def _init(self, run_job_id, name, *args, **kwargs):
        super(ValuePlaceholder, self)._init(*args, **kwargs)
        self.run_job_id = run_job_id
        self.name = name

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
                for key, value in ret_annotation.items():
                    self.parameters[key] = ValuePlaceholder(self.run_job_id, key, as_type=value)
            else:
                for key in ret_annotation:
                    self.parameters[key] = ValuePlaceholder(self.run_job_id, key)

    def get_result_id(self, name):
        if name not in self.parameters:
            raise Exception("Placeholder has no parameter: '%s'" % name)

        return self.worker_elf.mycellium.get_result_id(self.run_job_id, name)

    def __getitem__(self, key):
        if self.is_none:
            return None

        return self.parameters[key]

    def __str__(self):
        if self.is_none:
            return "*-%s: None-*"% self.__class__.__name__

        return "*-%s: %s-*" %( self.__class__.__name__, str(self.parameters) )

    def __repr__(self):
        return str(self)

class TaskParameters:

    def __init__(self, fct):
        from inspect import signature

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

    def get_parameters(self):
        def _add_param(value, uid, value_type, expression):
            ret = {
                "uid": uid,
                "type": value_type,
                "value": value,
                "expression": expression,
            }
            return ret

        def _rec_find_parameters(obj_key_value, embedding_operation):
            args = {}
            for param_name, value in obj_key_value:
                placeholder = None
                if isinstance(value, ValuePlaceholder):
                    placeholder = value
                    value = None
                else:
                    value_type = self.get_storable_type(value)
                    iterator = None
                    if type(value) is dict:
                        iterator = value.items()
                        new_value = {}
                        expression = "{parent_uid}[{self_name}] = {self_value}"
                    elif type(value) in [list, tuple]:
                        iterator = enumerate(value)
                        new_value = []
                        expression = "{parent_uid}.append({self_value})"
                   
                    if not iterator is None:
                        embeddings = _rec_find_parameters(iterator, new_embedding_operation)
                        
                    # if len(embeddings) > 0:
                        # value = None

                args[param_name] = _add_param(new_value, uid=ut.getuid(), value_type=value_type, expression=expression)

            return args

        ret = _rec_find_parameters(self.final_args.items(), None)

        return ret
        
    # def get_parameters(self):
    #     def _add_param(value, uid, value_type, expression):
    #         ret = {
    #             "uid": uid,
    #             "type": value_type,
    #             "value": value,
    #             "expression": expression,
    #         }
    #         return ret

    #     def _rec_find_parameters(obj_key_value, embedding_operation):
    #         args = {}
    #         for param_name, value in obj_key_value:
    #             placeholder = None
    #             if isinstance(value, ValuePlaceholder):
    #                 placeholder = value
    #                 value = None
    #             else:
    #                 value_type = self.get_storable_type(value)
    #                 iterator = None
    #                 if type(value) is dict:
    #                     iterator = value.items()
    #                     new_value = {}
    #                     expression = "{parent_uid}[{self_name}] = {self_value}"
    #                 elif type(value) in [list, tuple]:
    #                     iterator = enumerate(value)
    #                     new_value = []
    #                     expression = "{parent_uid}.append({self_value})"
                   
    #                 if not iterator is None:
    #                     embeddings = _rec_find_parameters(iterator, new_embedding_operation)
                        
    #                 # if len(embeddings) > 0:
    #                     # value = None

    #             args[param_name] = _add_param(new_value, uid=ut.getuid(), value_type=value_type, expression=expression)

    #         return args

    #     ret = _rec_find_parameters(self.final_args.items(), None)

    #     return ret

    def get_parameters_bck(self):
        def _add_param(value, value_type, static, embeddings, embedding_operation, placeholder):
            ret = {
                "type": value_type,
                "value": value,
                "is_static": static,
                "is_embedded": not (embedding_operation is None),
                "embeddings": embeddings,
                "embedding_operation": embedding_operation,
                "has_embeddings": not (embeddings is None) and len(embeddings) > 0,
                "placeholder": placeholder
            }
            return ret

        def _rec_find_parameters(obj_key_value, embedding_operation):
            args = {}
            for param_name, value in obj_key_value:
                embeddings = {}
                placeholder = None
                if isinstance(value, ValuePlaceholder):
                    placeholder = value
                    value = None
                    static = False
                else:
                    value_type = self.get_storable_type(value)
                    static = True
                    iterator = None
                    if type(value) is dict:
                        iterator = value.items()
                        new_embedding_operation = "__setitem__"
                    elif type(value) in [list, tuple]:
                        iterator = enumerate(value)
                        new_embedding_operation = "__setitem__"
                    
                    if not iterator is None:
                        embeddings = _rec_find_parameters(iterator, new_embedding_operation)
                        
                    if len(embeddings) > 0:
                        value = None

                args[param_name] = _add_param(value, value_type, static, embeddings, embedding_operation, placeholder)

            return args
        
        ret = _rec_find_parameters(self.final_args.items(), None)

        return ret

    # def get_placeholder_parameters(self):
    #     args = {}
    #     for param_name, value in self.final_args.items():
    #         if isinstance(value, ValuePlaceholder):
    #             args[param_name] = value

    #     return args

    # def get_static_parameters(self):
    #     args = {}
    #     for param_name, value in self.final_args.items():
    #         if not isinstance(value, ValuePlaceholder):
    #             args[param_name] = value
    #     return args

    # def get_embedded_placeholder_parameters(self):
    #     args = {}
    #     for param_name, value in self.final_args.items():
    #         if type(value) is dict:
    #             iterator = value.items()
    #         elif type(value) is list:
    #             iterator = enumerate(value)
    #         emb_args = self.find_placeholders_in_key_value_iterrator(iterator)
    #         if len(emb_args) > 0:
    #             args[param_name] = {
    #                 "placeholders": emb_args,
    #                 "emebedding_function": "__setitem__"
    #             }

    #     return args

class JOB:
    """docstring for JOB"""
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
        mycellium,
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
        self.mycellium = mycellium
        self.return_placeholder=return_placeholder

    def commit(self):
        self.mycellium.push_job(self)

class Task:
    """docstring for Task"""
    def __init__(self, machine_elf, function, name):
        self.machine_elf = machine_elf
        self.function = function
        self.name = name
        self.parameters = None
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
            self.parameters = TaskParameters(self.function)
            self.parameters.set_parameters(*args, **kwargs)
            self.parameters.validate()

            now = ut.gettime()
            
            return_placeholder = TaskReturnPlaceHolder(worker_elf=self.machine_elf.uid, task_function=self.function, run_job_id=run_job_id)
            return_placeholder.make_placeholder()

            job = JOB(
                task = self,
                run_job_id = run_job_id,
                worker_elf = self.machine_elf,
                parameters = self.parameters,
                submit_date = now,
                start_date = None,
                completion_date = None,
                status = custom_types.STATUS["PENDING"],
                mycellium = self.machine_elf.mycellium,
                return_placeholder=return_placeholder
            )
            
            job_id = job.commit()

            return return_placeholder

        return _wrapped

    def run(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.wrap( *args, **kwargs )()

    def __str__(self):
        return "*-Task '%s.%s': %s -*" % (self.machine_elf.uid, self.name, self.signature)

    def __repr__(self):
        return str(self)

class MachineElf:
    """docstring for MachineElf"""

    def __init__(self, uid, mycellium):
        self.uid = ut.legalize_key(uid)
        self.mycellium = mycellium
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
        self.mycellium.register_machine_elf(self, store_source)

    def get_jobs(self):
        return self.mycellium.get_jobs(self.uid)

    def is_job_ready(self, parameters:dict, embedded_params:dict):
        import custom_types
        params_ready = not (custom_types.EmptyParameter in parameters.values() )
        
        for key, value in embedded_params.items():
            if value is custom_types.EmptyParameter:
                return False
        
        return params_ready

    def start_jobs(self, store_failures=True, raise_exceptions=True):
        jobs = self.mycellium.get_received_jobs(self.uid)
        for job in jobs:
            params = self.mycellium.get_job_parameters(job["id"], embedded=False)
            params.update( self.mycellium.get_job_static_parameters(job["id"]) )
            embedded_params = self.mycellium.get_job_parameters(job["id"], embedded=True)
            
            for emb_value in embedded_params.values():
                value = emb_value["value"]
                emb = emb_value["embedding"]
                parent_obj = params[ emb["parent_parameter_name"] ]
                insert_fct = getattr(parent_obj, emb["embedding_function"])
                insert_fct( int(emb["self_name"]), value)

            if job["status"]!= custom_types.STATUS["DONE"] and self.is_job_ready(params, embedded_params):
                self.run_task(job["id"], job["task"]["name"], params, store_failures=store_failures, raise_exceptions=raise_exceptions)

    def run_task(self, job_id:str, task_name:str, parameters:dict, store_failures:bool, raise_exceptions:bool):
        import sys
        try:
            task = getattr(self, task_name)
            self.mycellium.start_job(job_id)
            ret = task.run(**parameters)
            self.mycellium.store_results(job_id, ret)
            self.mycellium.update_job_status(job_id, custom_types.STATUS["DONE"])
            self.mycellium.complete_job(job_id)
        except Exception as exp:
            if store_failures:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.mycellium.register_job_failure(exc_type, exc_value, exc_traceback, job_id)
            
            if raise_exceptions:
                raise exp

        return ret
