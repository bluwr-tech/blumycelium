import utils as ut
from icecream import ic
import uuid

class ValuePlaceholder:

    def __init__(self, return_job_unique_id, parameter_key):
        self.return_job_unique_id = return_job_unique_id
        self.parameter_key = parameter_key

    def __str__(self):
        return "<ValuePlaceholder: parameter key: '%s', return key: '%s'>" %(self.parameter_key, self.return_job_unique_id)

    def __repr__(self):
        return str(self)

class ReturnPlaceHolder:
    """docstring for ReturnPlaceHolder"""
    def __init__(self, from_elf, task_function, job_unique_id):
        super(ReturnPlaceHolder, self).__init__()
        self.job_unique_id = job_unique_id
        self.task_function = task_function
        self.from_elf = from_elf
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
                self.parameters[key] = ValuePlaceholder(self.job_unique_id, key)

    def __getitem__(self, key, value):
        if self.is_none:
            return None

        return self.parameters[key]

    def __str__(self):
        if self.is_none:
            return "<ReturnPlaceHolder: None>"

        return "<ReturnPlaceHolder: %s>" % str(self.parameters)

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
        task_name,
        public_id,
        to_elf_uid,
        submit_date,
        parameters,
        static_parameters,
        start_date,
        completion_date,
        status,
        mycellium
    ):
        self.task_name=task_name
        self.public_id=public_id
        self.to_elf_uid=to_elf_uid
        self.submit_date=submit_date
        self.parameters=parameters
        self.static_parameters=static_parameters
        self.start_date=start_date
        self.completion_date=completion_date
        self.status=status
        self.mycellium = mycellium

    def commit(self):
        self.mycellium.push_job(self)

class MachineElf:
    """docstring for MachineElf"""

    def __init__(self, uid, mycellium):
        super(MachineElf, self).__init__()
        self.uid = ut.legalize_key(uid)
        self.mycellium = mycellium
    
    def register(self, store_source):
        self.mycellium.register_machine_elf(self, store_source)

    def get_jobs(self):
        return self.mycellium.get_jobs(self.uid)

    def check_job_ready(self, job_id):
        self.mycellium.is_ready(job_id)

    def start_jobs(self):
        jobs = self.mycellium.get_received_jobs(self.uid)
        for job in jobs:
            if self.check_job_ready(job):
                self.run_task(job)

    def run_task(self, job):
        task = getattr(self, job["task_name"])
        kwargs = self.mycellium.get_arguments(job["arguments_id"])
        
        try:
            ret = task(kwargs)
        except:
            self.mycellium.c(job, self.mycellium.STATUS_FAILED)
        
        self.mycellium.update_job_status(job, self.mycellium.STATUS_DONE)
        self.mycellium.push_job(job["receiver"], ret)

        return ret

    # def make_parameters(self, valued_parameters, placeholders):
    #     def _make_parameter(value):
    #         if isinstance(value, ValuePlaceholder):
    #             return {
    #                 "value": None,
    #                 "pending": self.mycellium.STATUS_PENDING
    #             }
    #         return {
    #             "value": value,
    #             "pending": self.mycellium.STATUS_READY
    #         }
        
    #     params = {}
    #     for dct in (valued_parameters, placeholders):
    #         for k_param, v_param in dct.items():
    #             params[k_param] = _make_parameter(v_param)

    #     return params

    def register_job(self, task_name, params, job_id):
        static_parameters = params.get_static_parameters()
        placeholder_parameters = params.get_placeholder_parameters()

        now = ut.gettime()
        job = JOB(
            task_name = task_name,
            public_id = job_id,
            to_elf_uid = self.uid,
            submit_date = now,
            parameters = placeholder_parameters,
            static_parameters = static_parameters,
            start_date = None,
            completion_date = None,
            status = self.mycellium.STATUS_PENDING,
            mycellium = self.mycellium
        )
        job.commit()

    def task_wrap(self, task_fct):
        def _wrapper(*args, **kwargs):
            job_id = str(uuid.uuid4())
            params = Parameters(task_fct)
            params.set_parameters(*args, **kwargs)
            params.validate()

            self.register_job(task_fct, params, job_id)

            ret = ReturnPlaceHolder(from_elf=self.uid, task_function=task_fct, job_unique_id=job_id)
            ret.make_placeholder()
            return ret

        return _wrapper

    def __getattr__(self, key):
        if hasattr(self, "task_" + key):
            value = getattr(self, "task_" + key)
            ret = self.task_wrap(value)
        else:
            ret = getattr(self, key)
        return ret
