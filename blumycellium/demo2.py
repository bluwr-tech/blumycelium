from icecream import ic
import uuid
import time
import inspect
import pyArango.theExceptions as exc

class Jobs(Collection) :
    _fields = {
        # "public_id" : job_id,
        "task" : {
            "name": Field(validators = [VAL.NotNull()]),
            "signature": {
                Field(validators = [VAL.NotNull()]),
            },
            "source_code": Field(),
            "documentation": Field(),
            "revision": Field(),
        },
        "worker" : {
            "id": Field(validators = [VAL.NotNull()]),
            "documentation": Field(),
            "revision": Field(),
        },
        "submit_date" : Field(validators = [VAL.NotNull()]),
        "start_date": Field(),
        "completion_date": Field(),
        "status": Field(validators = [VAL.NotNull()])
        
        "error_type": Field(),
        "error_traceback": Field(),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Worker(Collection) :
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

class Results(Edges) :
    _fields = {
        "submit_date" : Field(validators = [VAL.NotNull()]),
        "value" : Field(validators = [VAL.NotNull()]),
        "completion_date": Field(),
        "status": Field(validators = [VAL.NotNull()])
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Results_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("Results", fromCollections = ["Workers"], toCollections = ["Workers"]),
    ) 
    _orphanedCollections = []

class Jobs_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("Jobs", fromCollections = ["Workers"], toCollections = ["Workers"]),
    ) 
    _orphanedCollections = []

def _none_if_exception_or_empty(self, method, inspect_fct):
    ret = None
    try:
        ret = inspect_fct(method)
        if len(ret) == 0: ret = None
    except Exception as e:
        pass

    return ret

def gettime():
    import time
    return time.time()

class Mycellium:
    """docstring for Mycellium"""
    def __init__(self, connection, name, collections, graphs, users_to_create):
        self.connection = connection
        self.name = name
        self.db_name = "BLUMYC_" + name

        self.collections = collections
        self.graphs = graphs
        self.users_to_create = users_to_create
        self.db = self._init_dB()
        self.init()

    def init(self) :
        print("Initializing %s..." % self.db_name)    
        print("-- init collections")
        self._init_collections(self.db)
        print("-- init graphs")
        self._init_graphs(self.db)
        # print("-- init indexes")
        # self._init_indexes(self.db)
        print("-- init users")

        for user in self.users_to_create :
            self._init_user(self.connection, self.db_name, user["username"], user["password"])
        print("--")

    def _init_dB(self) :
        from pyArango.theExceptions import CreationError

        print("Creating database", self.db_name)
        try :
            return self.connection.createDatabase(self.db_name)
        except CreationError as e :
            print("Database Creation error %s: => %s" % (self.db_name, e.message))

            try :
                return self.connection[self.db_name]
            except :
                raise e

    def _init_collections(self, db, purge=False) :
        import pyArango.collection as COL

        for c in self.collections :
            if c.lower() not in ("collection", "edges", "field") :
                print("Creating collection", c)
                try :
                    db.createCollection(c, allowUserKeys=True)
                except Exception as e :
                    print("Collection Creation error: =>", e)

    def _init_graphs(self, db) :
        # import pyArango.graph as GR

        for g in self.graphs :
            if g.lower() != "graph":
                print("Creating graph", g)
                try :
                    db.createGraph(g)
                except Exception as e :
                    print("Graph Creation error (%s): =>" %g, e)
    
    def _init_user(self, connection, dbName, username, password) :
        import time
        
        print("creating user: %s" % username)
        
        u = connection.users.createUser(username, password)
        u["extra"] = "Created on: %s, by automatic setup" % time.ctime()
        try :
            u.save()
        except Exception as e1 :
            print("Can't create user: '%s' -> " % username, e1)
            try :
                u = connection.users.fetchUser(username)
            except Exception as e2 :
                raise UserCreationError("Unable to get user: '%s' -> " % username, e2)
        u.setPermissions(dbName, True)

    def register_worker(self, worker, store_code):
        source = _none_if_exception_or_empty(worker.__class__, inspect.getsource)
        revision = str( source )
        documentation = _none_if_exception_or_empty(worker.__class__, inspect.get_clean_doc)

        try:
            worker_doc = self.db["Workerss"][self.uid]
            worker_doc["revisions"]["dates"].append(gettime())
            worker_doc["revisions"]["dates"] = worker_doc["revisions"]["dates"]
            worker_doc["revisions"]["hashes"].append(last_revision)
            worker_doc["revisions"]["hashes"] = worker_doc["revisions"]["hashes"]
        except exc.DocumentNotFound:
            worker_doc = self.db["Workerss"].createDocument()
            worker_doc["creation_date"] = gettime()
            worker_doc["revisions"]["dates"] = [worker_doc["creation_date"]]
            worker_doc["revisions"]["hashes"] = [revision]

        worker_doc["documentation"] = documentation
        worker_doc["last_revision"] = last_revision
        if store_code:
            worker_doc["source"] = source

        worker_doc.save()

    def get_job_parameters(job):
        pass
    
    def update_job_status(self, *args, **kwargs):
        pass

    def push_job(self, *args, **kwargs):
        pass
 
    def get_received_jobs(self, *args, **kwargs):
        pass
 
    def get_jobs(self, *args, **kwargs):
        pass
 

class ABC_Worker:
    """docstring for ABC_Worker"""
    STATUS_PENDING=0
    STATUS_READY=1
    STATUS_DONE=2
    STATUS_FAILED=-1
    STATUS_UPSTREAM_FAILED=-2
    STATUS_EXPIRED=-3

    def __init__(self, uid, mycellium):
        super(ABC_Worker, self).__init__()
        self.uid = uid
        self.mycellium = mycellium

    def get_jobs(self):
        return self.mycellium.get_jobs(self.uid)

    def check_job_ready(self, job);
        for param, value in job["parameters"].items():
            if value["status"] != self.STATUS_READY:
                return False
        return True

    def start_jobs(self):
        jobs = self.mycellium.get_received_jobs(self.uid)
        for job in jobs:
            if self.check_job_ready(job):
                self.run_task(job)

    def task_pong(self, value):
        """for testing simply return the value with the workers unique ids"""
        return value + "_" + str(self.uid)
    
    def run_task(self, job):
        task = getattr(self, job["task_name"])
        kwargs = self.mycellium.get_arguments(job["arguments_id"])
        
        try:
            ret = task(kwargs)
        except:
            self.mycellium.c(job, self.STATUS_FAILED)
        
        self.mycellium.update_job_status(job, self.STATUS_DONE)
        self.mycellium.push_job(job["receiver"], ret)

        return ret

    def make_parameters(self, valued_parameters, placeholders):
        def _make_parameter(value)
            if isinstance(value, ValuePlaceholder):
                return {
                    "value": None,
                    "pending": self.STATUS_PENDING
                }
            return {
                "value": value,
                "pending": self.STATUS_READY
            }
        
        params = {}
        for dtc in (valued_parameters, placeholders):
            for k_param, v_param in dct.items():
                params[k_param] = _make_parameter(v_param)

        return params

    def register_job(self, task_name, params, job_id):
        valued_parameters = params.get_valued_parameters()
        placeholders = params.get_placeholders()

        store_parameters = self.make_parameters(valued_parameters, placeholders)
        job = JOb(
            task_name = task_name,
            public_id = job_id,
            worker_uid = self.uid,
            submit_date = date,
            parameters = store_parameters,
            submit_date = time.time(),
            start_date=None,
            completion_date=None,
            status=self.STATUS_PENDING
        )
        self.mycellium.push_job(Job)

    def task_wrap(self, task_fct):
        def _wrapper(*args, **kwargs):
            job_id = str(uuid.uuid4())
            params = Parameters(task_fct)
            params.set_parameters(*args, **kwargs)
            params.validate()

            self.register_job(task_name, params, job_id)

            ret = ReturnPlaceHolder(task_fct, job_id)
            ret.make_placeholder()
            return ret

        return _wrapper

    def __getattr__(self, key):
        if hasattr(self, "task_" + key):
            value = getattr(self, "task_" + key)
            ret = self.task_wrap(value)
        else:
            ret = getattr(self, key)
        return key

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
    def __init__(self, task_function, job_unique_id):
        super(ReturnPlaceHolder, self).__init__()
        self.job_unique_id = job_unique_id
        self.task_function = task_function
        self.parameters = {}

    def make_placeholder(self):
        from inspect import signature, _empty

        sig = signature(self.task_function)
        ret_annotation = sig.return_annotation

        if (ret_annotation is _empty) or (type(ret_annotation) not in [list, tuple]) :
            raise Exception("Task return annotation cannot be empty, expecting tuple or list of parameter keys")

        for key in ret_annotation:
            self.parameters[key] = ValuePlaceholder(self.job_unique_id, key)

    def __getitem__(self, key, value):
        return self.parameters[key]

    def __str__(self):
        return "<ReturnPlaceHolder: %s>" % str(self.parameters)

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
                if not parameters[param].annotation is _empty and:
                    param_clas = parameters[param].annotation
                elif not parameters[param].default is _empty :
                    param_clas = type(parameters[param].default)

                if param_clas and not isinstance(value, param_clas):
                    raise Exception("Param '{param}' has the wrong type {type} expected {exp})".format(param=param, type=type(value), exp=param_clas))
        return True

    def get_placeholders():
        args = {}
        for param, value in self.final_args.items():
            if isinstance(value, ValuePlaceholder):
                args[param] = value
        return args

    def get_valued_parameters():
        args = {}
        for param, value in self.final_args.items():
            if not isinstance(value, ValuePlaceholder):
                args[param] = value
        return args

# def task_wrap(task_fct):
#     def _wrapper(*args, **kwargs):
#         params = Parameters(task_fct)
#         params.set_parameters(*args, **kwargs)
#         params.validate()

#         ret = ReturnPlaceHolder(task_fct)
#         ret.make_placeholder()
#         return ret
#     return _wrapper

# from inspect import signature

# def fct(k, a:int, b:str, c=3) -> Return("a", "b"):
#     ic(k, a, b)

# sig = signature(fct)
# print(dir(sig))
# print(sig.parameters)
# print(sig.parameters["k"])
# print(dir(sig.parameters["k"]))
# print(sig.parameters["k"].annotation)
# print(sig.parameters["k"].default)
# print(sig.parameters["a"].annotation)
# print(sig.parameters["c"].annotation)
# print(sig.parameters["c"].default)
# print(sig.return_annotation)

if __name__ == '__main__':
    # mycellium = DictMycellium()
    
    # work1 = ABC_Worker(uid=1, mycellium)
    # work2 = ABC_Worker(uid=2, mycellium)
    
    # ret1 = work1.pong("ping1")
    # ret2 = work2.pong(ret["value"])

    # work1.start_jobs()
    # work2.start_jobs()

    def fct(k, a:int, b:int, c=3) -> ("a", "b"):
        return {"a": a, "b": b}

    ret = task_wrap(fct)(1, 2, 3)
    print(ret)
    