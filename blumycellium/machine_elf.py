import utils as ut
from icecream import ic
import uuid

class ValuePlaceholder:

    def __init__(self, return_run_id, parameter_key):
        self.return_run_id = return_run_id
        self.parameter_key = parameter_key

    def __str__(self):
        return "<ValuePlaceholder: parameter key: '%s', return key: '%s'>" %(self.parameter_key, self.return_run_id)

    def __repr__(self):
        return str(self)

class ReturnPlaceHolder:
    """docstring for ReturnPlaceHolder"""
    def __init__(self, worker_elf, task_function, run_id):
        self.task_function = task_function
        self.worker_elf = worker_elf
        self.run_id = run_id
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
            for key in ret_annotation:
                self.parameters[key] = ValuePlaceholder(self.run_id, key)

    def get_result_id(self, name):
        if name not in self.parameters:
            raise Exception("Placeholder has no parameter: '%s'" % name)

        return self.worker_elf.mycellium.get_result_id(self.run_id, name)

    def __getitem__(self, key, value):
        if self.is_none:
            return None

        return self.parameters[key]

    def __str__(self):
        if self.is_none:
            return "*-%s: None-*"% self.__class__.__name__

        return "*-%s: %s-*" %( self.__class__.__name__, str(self.parameters) )

    def __repr__(self):
        return str(self)

class Parameters:

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
    
    def validate(self):
        from inspect import _empty

        parameters = self.signature.parameters
        for param, value in self.final_args.items():
            if not isinstance(value, ValuePlaceholder):
                param_clas = None
                if not parameters[param].annotation is _empty :
                    param_clas = parameters[param].annotation
                elif not parameters[param].default is _empty :
                    param_clas = type(parameters[param].default)

                if param_clas and not isinstance(value, param_clas):
                    raise Exception("Param '{param}' has the wrong type {type} expected {exp})".format(param=param, type=type(value), exp=param_clas))
        return True

    def get_placeholder_parameters(self):
        args = {}
        for param, value in self.final_args.items():
            if isinstance(value, ValuePlaceholder):
                args[param] = value
        return args

    def get_static_parameters(self):
        args = {}
        for param, value in self.final_args.items():
            if not isinstance(value, ValuePlaceholder):
                args[param] = value
        return args

class JOB:
    """docstring for JOB"""
    def __init__(
        self,
        task,
        run_id,
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
        self.run_id=run_id
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
        self.revision = str( hashlib.sha256(self.source_code.encode("utf-8")).hexdigest() )
        self.documentation = ut.inpsect_none_if_exception_or_empty(self.function, "cleandoc")
        self.signature = ut.inpsect_none_if_exception_or_empty(self.function, "signature")

    def wrap(self, *args, **kwargs):
        args = args
        kwargs = kwargs
        run_id = str(uuid.uuid4())

        def _wrapped():
            self.parameters = Parameters(self.function)
            self.parameters.set_parameters(*args, **kwargs)
            self.parameters.validate()

            now = ut.gettime()
            
            return_placeholder = ReturnPlaceHolder(worker_elf=self.machine_elf.uid, task_function=self.function, run_id=run_id)
            return_placeholder.make_placeholder()
            
            job = JOB(
                task = self,
                run_id = run_id,
                worker_elf = self.machine_elf,
                parameters = self.parameters,
                submit_date = now,
                start_date = None,
                completion_date = None,
                status = self.machine_elf.mycellium.STATUS_PENDING,
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

        self.source = None
        self.revision = None
        self.documentation= None
        
        self.inspect_self()
        self.find_tasks()

    def inspect_self(self):
        import hashlib

        self.source = ut.inpsect_none_if_exception_or_empty(self.__class__, "getsource")
        self.revision = str( self.__class__.__name__ + hashlib.sha256(self.source.encode("utf-8")).hexdigest() )
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

    def is_job_ready(self, parameters:dict):
        import custom_types
        return not (custom_types.EmptyParameter in parameters.values() )

    def start_jobs(self, store_failures=True, raise_exceptions=True):
        jobs = self.mycellium.get_received_jobs(self.uid)
        for job in jobs:
            params = self.mycellium.get_job_parameters(job["id"])
            if job["status"]!= self.mycellium.STATUS_DONE and self.is_job_ready(params):
                self.run_task(job["id"], job["task"]["name"], params, store_failures=store_failures, raise_exceptions=raise_exceptions)

    def run_task(self, job_id, task_name, parameters:dict, store_failures, raise_exceptions):
        import sys
        try:
            task = getattr(self, task_name)
            ret = task.run(**parameters)
            self.mycellium.store_results(job_id, ret)
            self.mycellium.update_job_status(job_id, self.mycellium.STATUS_DONE)
        except Exception as exp:
            if store_failures:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.mycellium.register_job_failure(exc_type, exc_value, exc_traceback, job_id)
            
            if raise_exceptions:
                raise exp

        return ret
