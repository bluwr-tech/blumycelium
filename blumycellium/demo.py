
from pyArango.collection import Collection, Edges, Field

import pyArango.validation as VAL
import bluwrserver.consts as consts
import bluwrserver.include.models.custom_validators as CVAL
import pyArango.graph as GR
import pyArango.connection as ADB

from icecream import ic

import logging
logger = logging.getLogger(__name__)

class MycelliumError(Exception):
    """docstring for MycelliumError"""
    def __init__(self, message):
        super(MycelliumError, self).__init__()
        self.message = message
        logger.log(logging.ERROR, self.message)

    def str(self):
        return self.message

class PermissionError(MycelliumError):
    pass

class StatusChangeError(MycelliumError):
    pass

class TaskRegistrationError(MycelliumError):
    pass

class UserCreationError(MycelliumError):
    pass

class ElfkNotFoundError(MycelliumError):
    pass

class TaskNotFoundError(MycelliumError):
    pass

class MissingReturnAnnotation(MycelliumError):
    pass

class TaskWithoutSourceCode(MycelliumError):
    pass

def get_date():
    import time
    return time.time()

class Elves(Collection) :
    """Collection of all registered entities elves and bluwr"""
    _fields = {
        "name": Field(validators = [VAL.NotNull()]),
        "documentation": Field(validators = [VAL.NotNull()]),
        "creation_date": Field(validators = [VAL.NotNull()]),
        # "version": Field(validators = [VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Tasks(Collection) :
    """Collection of all registered entities elves and bluwr"""
    _fields = {
        "elf_name": Field(validators = [VAL.NotNull()]),
        "name": Field(validators = [VAL.NotNull()]),
        "creation_date": Field(validators = [VAL.NotNull()]),
        "documentation": Field(validators = [VAL.NotNull()]),
        "parameters": Field(validators = [VAL.NotNull()], default=dict),
        # "version": Field(validators = [VAL.NotNull()]),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Jobs(Edges) :
    _fields = {
        "creation_date": Field(validators = [VAL.NotNull()]),
        "status": Field(validators = [VAL.NotNull(), VAL.Enumeration(["unconfirmed", "pending", "revoked", "abandoned", "wip", "error", "success"])], default="unconfirmed"),
        "task_name": Field(validators = [VAL.NotNull()]),
        "join_task_name": Field(validators = [VAL.NotNull()]),
        "task_parameters": Field(validators = [VAL.NotNull()]),
        "public_key": Field(validators = [VAL.NotNull()]),
        "job_single_key": Field(validators = [VAL.NotNull()]),
        "job_number": Field(validators = [VAL.NotNull(), VAL.Numeric()], default=-1),
        "sender_stash": Field(),
        "receiver_stash": Field(),
        "return": Field(),
        "error_type": Field(),
        "error_traceback": Field(),
    }

    _validation = {
        "on_save": True,
        "on_set": False,
        "allow_foreign_fields": False
    }

class Jobs_graph(GR.Graph):
    _edgeDefinitions = (
        GR.EdgeDefinition("Jobs", fromCollections = ["Elves"], toCollections = ["Elves"]),
    ) 
    _orphanedCollections = []

class Mycellium:
    def __init__(self, connection, name, collections, graphs, users_to_create):
        self.connection = connection
        self.name = name
        self.db_name = "BLUMYC_" + name

        self.collections = collections
        self.graphs = graphs
        self.users_to_create = users_to_create
        self.db = self._init_dB()
    
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

    def register_elf(self, name, documentation, update=False):
        if not update:
            elf = self.db["Elves"].createDocument()
        else:
            elf = self.db["Elves"][name.lower()]
        elf["_key"] = name.lower()
        elf["name"] = name
        elf["creation_date"] = get_date()
        elf["documentation"] = documentation
        elf.save()
        logger.log(logging.INFO, "registered elf: %s" % elf["_key"])

    def register_task(self, elf, name, documentation, parameters, update=False):
        task_key = elf.name.lower() + "." + name.lower()

        if not update:
            task = self.db["Tasks"].createDocument()
        else:
            task = self.db["Tasks"][task_key]
        task["name"] = name

        if elf.name.lower() not in self.db["Elves"]:
            raise ElfkNotFoundError("There is no elf with the name: %s" % elf.name)
        task["elf_name"] = elf.name
        
        task["_key"] = task_key
        
        task["creation_date"] = get_date()
        task["documentation"] = documentation
        if type(parameters) is not dict:
            raise TaskRegistrationError("parameters must be dict: arg_name => {type: python type, documentation: textual documentation}")
            for key, value in parameters.keys():
                if type(value) is not dict or set(value.keys()) != {"type", "documentation"}: 
                   raise TaskRegistrationError("parameters must be dict: arg_name => {type: python type, documentation: textual documentation}. parameters: %s has incorrect schema" % key)
        
        task["parameters"] = parameters
        logger.log(logging.INFO, "registered task: %s of elf %s" % (elf.name, task["_key"]))
        task.save()

    def push_job(self, from_elf, to_elf, task_name, task_parameters, public_key):
        """
        """
        graph = self.db.graphs["Jobs_graph"]
        task_key = (to_elf.name.lower() + "." + task_name).lower()

        job_single_key = from_elf.name.lower() + "X" + to_elf.name.lower() + "."+ task_key

        if task_key not in self.db["Tasks"]:
            raise TaskNotFoundError("There's no task: %s" % task_key)

        data = {
            "creation_date": get_date(),
            "public_key": public_key,
            "status": "pending",
            "task_name": task_name,
            "task_parameters": task_parameters,
            "job_single_key": job_single_key,
            "job_number": -1
        }
        new_job = graph.link("Jobs", to_elf.data, to_elf.data, edgeAttributes=data)

        aql = """
            FOR job in Jobs
                FILTER job._from == @from_elf_id
                FILTER job.status == "pending"

                RETURN job
        """

        bind_vars = {"from_elf_id": from_elf.data["_id"]}
        all_jobs = [ job for job in self.db.AQLQuery(aql, bindVars=bind_vars, batchSize = 100, rawResults=True) ]
        return {
            "new_job": new_job,
            "all_jobs": all_jobs,
            "new_job_id": new_job["_id"]
        }

    def confirm_job(self, job_id):
        job = self.db["Jobs"][job_id]
        job["status"] = "pending"
        job.save()
        return job

    def _get_jobs(self, elf_id, status, received=True):
        if received:
            direction = "_to"
        else:
            direction = "_from"

        aql = """
            FOR job in Jobs
                FILTER job.{direction} == @elf_id
                FILTER job.status == @status

                RETURN job
        """.format(direction=direction)

        bind_vars = {"elf_id": elf_id, "status": status}
        return [ job for job in self.db.AQLQuery(aql, bindVars=bind_vars, batchSize = 100, rawResults=True) ]

    def get_received_jobs(self, elf, status="pending"):
        return self._get_jobs(elf.data["_id"], status, received=True)

    def get_sent_jobs(self, elf, status="pending"):
        return self._get_jobs(elf.data["_id"], status, received=False)

    def _get_received_job(self, job_id, elf_id):
        return self._get_job(job_id, elf_id, received=True)

    def _get_sent_job(self, job_id, elf_id):
        return self._get_job(job_id, elf_id, received=False)

    def terminate_job(self, job_id, elf, status, return_value=None, error_type=None, error_traceback=None, termination_reason=None):
        job = None
        if status in ["revoked"]:
            job = self._get_sent_job(job, elf.data["_id"])
            if job["status"] != "pending":
                raise StatusChangeError("A job can only be revoked if it's status is 'pending'")
        elif status in ["abandoned", "error", "success"]:
            job = self._get_received_job(job, elf.data["_id"])
        else:
            raise StatusChangeError("Unkown status: %s" % status)

        if jos is None:
            raise StatusChangeError("Could not find a job for this description. Some status can only be applied to sent jobs, and other to received jobs.")
    
        job["return"] = return_value
        job["error_type"] = error_type
        job["error_traceback"] = error_traceback
        job["error_traceback"] = termination_reason
        job["status"] = status
        job.save()

    def has_elf(self, elf):
        return elf.name.lower() in self.db["Elves"]

    def get_elf_document(self, elf):
        return self.db["Elves"][elf.name.lower()]

class ABC_Elf(object):
    """docstring for ABC_Elf"""
    def __init__(self, mycellium):
        super(ABC_Elf, self).__init__()
        self.mycellium = mycellium
        self.tasks = {}
        self.auto_inspect()

    def _add_task(self, task_name, method):
        import inspect
        import hashlib

        def _none_if_exception_or_empty(method, inspect_fct):
            ret = None
            try:
                ret = inspect_fct(method)
                if len(ret) == 0: ret = None
            except Exception as e:
                pass

            return ret

        signature = inspect.signature(method)

        return_annotation = signature.return_annotation
        if return_annotation is signature.empty:
            raise MissingReturnAnnotation(f"Method {task_name} is missing a return annotations")

        parameters = {}

        none_if_signature_empty = lambda x: None if x is signature.empty else x
        
        documentation = _none_if_exception_or_empty(method, inspect.getdoc)
        source = _none_if_exception_or_empty(method, inspect.getsource)

        if source is None:
            raise TaskWithoutSourceCode(f"Task {task_name} has no retreivable source code")

        version = str( hashlib.sha1(source.encode("utf-8")).hexdigest() )

        for param_name, param in signature.parameters.items():
            parameters[param_name] = {
                "declaration": str(param),
                "type": str(param.annotation),
                "default": none_if_signature_empty(param.default)
            }

        self.tasks[task_name] =  {
                "name": task_name,
                "documentation": documentation,
                "source_code": source,
                "signature": str(signature),
                "parameters": parameters,
                "return": return_annotation,
                "version": version
            }

    def auto_inspect(self):
        import inspect

        for name, member in inspect.getmembers(self):
            if name.startswith("task_") and inspect.ismethod(member):
                ic(name, member)
                self._add_task(name, member)

        ic(self.tasks)

    def register(self, update):
        self.mycellium.register_elf(name=self.name, documentation="the first dummy elf", update=update)

    def register_tasks(self, update):
        """find all function begining by 'task_' """
        raise NotImplemented("Abstract function")

    def install(self, update):
        print("installing:", self.name)
        self.register(update)
        self.register_tasks(update)

    def run(self):
        jobs = self.mycellium.get_received_jobs(self)
        for job in jobs :
            fct = getattr(self, "task_" + job["task_name"])
            try :
                return_value = fct(**job["task_parameters"])
            except Exception as exc:
                self.mycellium.terminate_job(job, self, "error", return_value=None, error_type=exc.__class__.__name__, error_traceback=exc.traceback, termination_reason="Exception")
            self.mycellium.terminate_job(job, self, "success", return_value)

    def join(self):
        jobs = self.mycellium.get_sent_jobs(self)
        for job in jobs :
            fct = getattr(self, "task_" + job["join_task_name"])
            try :
                return_value = fct(**job["task_parameters"])
            except Exception as exc:
                self.mycellium.terminate_job(job, self, "error", return_value=None, error_type=exc.__class__.__name__, error_traceback=exc.traceback, termination_reason="Exception")
            self.mycellium.terminate_job(job, self, "success", return_value)

    def _get_jobs(self, received, status_restriction=None):
        from collections import defaultdict

        if received:
            jobs = self.mycellium.get_received_jobs(self)
        else:
            jobs = self.mycellium.get_sent_jobs(self)
        
        ret = defaultdict()
        for job in jobs :
            if status_restriction is None or job["status"] in status_restriction:
               ret[job["status"]].append(job)

        return ret

    def get_sent_jobs(self, status_restriction=None):
        return self._get_jobs(status, received=False, status_restriction=status_restriction)

    def get_received_jobs(self, status_restriction=None):
        return self._get_jobs(status, received=True, status_restriction=status_restriction)

    def check_doorstep(self):
        """return all sent jobs that have finished"""
        return self.get_sent_jobs(status_restriction=["success"])

    def check_failed(self):
        """return all sent jobs that have finished with errors / abandoned"""
        return self.get_sent_jobs(status_restriction=["error", "abandoned"])

    def assign(self, to_elf, task_name, task_parameters, public_key ):
        """assign a task to an elf"""
        self.mycellium.push_job(self, to_elf, task_name, task_parameters, public_key)

    def abandon(self, job_name, reason=None):
        self.mycellium.terminate_job(job, self, "abandoned", return_value=None, error_type=None, error_traceback=None, termination_reason=reason)

    def revoke(self, job_name, reason=None):
        self.mycellium.terminate_job(job, self, "revoked", return_value=None, error_type=None, error_traceback=None, termination_reason=reason)

    def abandon_all(self, job_name, reason=None):
        jobs = self.mycellium.get_received_jobs(self)
        for job in jobs :
            self.abandon(self, job["name"], reason=reason)

    def revoke_all(self, job_name, reason=None):
        for job in jobs :
            self.revoke(self, job["name"], reason=reason)

    @property
    def data(self):
        return self.mycellium.get_elf_document(self)

class DummyElf_Prefix(ABC_Elf):
    """docstring for DummyElf_Prefix"""
    def __init__(self, mycellium, name):
        super(DummyElf_Prefix, self).__init__(mycellium)
        self.name = name
        self.version = 1.1

        # self.tasks = [
        #     {
        #         "name": "say_my_name",
        #         "documentation": "print the class name with a prefix",
        #         "parameters":{
        #             "prefix": {
        #                 "type": str,
        #                 "documentation": "a prefix to append before the name"
        #             }
        #         },
        #         "return": None
        #         # "version": "1.0"
        #     }
        # ]
        
    def task_say_my_name(self, prefix:str) -> None:
        """Print class name and add prefix to it"""
        print(prefix + self.__class__.__name__)

    def register_tasks(self, update):
        for task in self.tasks:
            self.mycellium.register_task(elf=self, name=task["name"], documentation=task["documentation"], parameters=task["parameters"], update=update)

class DummyElf_Sufix(ABC_Elf):
    """docstring for DummyElf_Sufix"""
    def __init__(self, mycellium, name):
        super(DummyElf_Sufix, self).__init__(mycellium)
        self.name = name
        self.version = 1.1

        self.tasks = [
            {
                "name": "task_say_my_name",
                "documentation": "print the class name with a sufix",
                "parameters":{
                    "sufix": {
                        "type": str,
                        "documentation": "a sufix to append after the name"
                    }
                },
                "return": None
                # "version": "1.0"
            }
        ]

    def task_say_my_name(self, sufix):
        print(self.__class__.__name__ + sufix)

    def register_tasks(self, update):
        for task in self.tasks:
            self.mycellium.register_task(elf=self, name=task["name"], documentation=task["documentation"], parameters=task["parameters"], update=update)

class KnowMyName(ABC_Elf):
    def __init__(self, mycellium, name):
        super(KnowMyName, self).__init__(mycellium)
        self.name = name.lower()
        self.mycellium = mycellium
        self.version = 1.1

    def register_tasks(self, update):
        pass

    def install(self, update):
        print("installing:", self.name)
        self.register(update)

class Orchestrater(ABC_Elf):
    """An elf that dispatches several pushes to many elves, compiles them and sends a push to original sender"""
    def __init__(self, name):
        super(Orchestrater, self).__init__()
        self.name = name
    
    def join(self):
        import uuid
        public_key = str(uuid.uuid4())

if __name__ == '__main__':
    collections = ["Elves", "Tasks", "Jobs"]
    graphs = ["Jobs_graph"]
    users_to_create=[ {"username": "mycellium", "password": "mycellium"}]
    connection = ADB.Connection(
        arangoURL = "http://127.0.0.1:8529",
        username = "root",
        password = "root"
    )

    myc = Mycellium(
        connection=connection,
        name="mycellium",
        collections=collections,
        graphs=graphs,
        users_to_create=users_to_create
    )
    myc.init()

    dp = DummyElf_Prefix(myc, "prefix")
    dp.install(update=True)

    ds = DummyElf_Sufix(myc, "sufix")
    ds.install(update=True)

    kn = KnowMyName(myc, "My_name_is_KN")
    kn.install(update=True)

    kn.mycellium.push_job(kn, dp, "task_say_my_name", {"prefix": " <======AmericAAA Fuck YEah!!!!-----> "}, kn.name)
    kn.mycellium.push_job(kn, ds, "task_say_my_name", {"sufix": " <======AmericAAA Fuck YEah!!!!-----> "}, kn.name)

    print("ds rec", ds.mycellium.get_received_jobs(ds))
    print("dp rec", dp.mycellium.get_received_jobs(dp))

    print("ds sent", ds.mycellium.get_sent_jobs(ds))
    print("dp sent", dp.mycellium.get_sent_jobs(dp))

    dp.run()
    ds.run()
