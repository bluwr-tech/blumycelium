
import uuid
import pyArango.theExceptions as a_exc
import utils as ut
import custom_types

import models as mod

from icecream import ic
ic.configureOutput(includeContext=True)

import logging
logger = logging.getLogger("BLUMYCELLIUM")

class Mycellium:
    """docstring for Mycellium"""

    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
        self.db_name = "BLUMYC_" + name

        self.collections = mod.COLLECTIONS
        self.graphs = mod.GRAPHS

        self.db = None

        if not self.connection.hasDatabase(self.db_name):
            logger.warning("Warning: Database %s does not exist. To create it run self.init with init_db=True" % self.db_name)
        else:
            self.db = self.connection[self.db_name]

    def _init_db(self) :
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

    def init(self, init_db=False, users_to_create=None) :
        if init_db:
            self.db = self._init_db()

        if self.db is None:
            raise Exception("Cannot continue with the initialisation because database does not exist. Try runing init with init_db=True")

        logger.info("Initializing %s..." % self.db_name)    
        logger.info("-- init collections")
        self._init_collections(self.db)
        logger.info("-- init graphs")
        self._init_graphs(self.db)
        logger.info("-- init indexes")
        self._init_indexes(self.db)
        logger.info("-- init users")

        if users_to_create:
            for user in self.users_to_create :
                self._init_user(self.connection, self.db_name, user["username"], user["password"])
    
    def drop_jobs(self):
        """delete all information related to jobs"""
        for collection in ["Jobs", "Results", "Failures", "Parameters", "JobFailures"]:
            self.db[collection].truncate() 

    def _init_collections(self, db, purge=False) :
        for collection in self.collections :
            if collection.lower() not in ("collection", "edges", "field") :
                logger.info("Creating collection", collection)
                try :
                    db.createCollection(collection, allowUserKeys=True)
                except Exception as exp :
                    logger.info("Collection Creation error: =>", exp)

    def _init_graphs(self, db) :
        for graph in self.graphs :
            if graph.lower() != "graph":
                logger.info("Creating graph", graph)
                try :
                    db.createGraph(graph)
                except Exception as exp :
                    logger.info("Graph Creation error (%s): =>" %graph, exp)
    
    def _init_user(self, connection, dbName, username, password) :
        logger.info("creating user: %s" % username)
        
        user = connection.users.createUser(username, password)
        user["extra"] = "Created on: %s, by automatic setup" % ut.gettime()
        try :
            user.save()
        except Exception as e1 :
            logger.info("Can't create user: '%s' -> " % username, e1)
            try :
                user = connection.users.fetchUser(username)
            except Exception as e2 :
                raise UserCreationError("Unable to get user: '%s' -> " % username, e2)
        u.setPermissions(dbName, True)

    def _init_indexes(self, *args, **kwargs):
        logger.info("No indexes defined")

    def register_machine_elf(self, machine_elf, store_source):
        now = ut.gettime()
        first_register = False
        try:
            elf_doc = self.db["MachineElves"][machine_elf.uid]
            elf_doc["revisions"]["dates"].append(now)
            elf_doc["revisions"]["dates"] = elf_doc["revisions"]["dates"]
            elf_doc["revisions"]["hashes"].append(machine_elf.revision)
            elf_doc["revisions"]["hashes"] = elf_doc["revisions"]["hashes"]
        except a_exc.DocumentNotFoundError:
            elf_doc = self.db["MachineElves"].createDocument()
            elf_doc["_key"] = machine_elf.uid
            elf_doc["creation_date"] = now
            elf_doc["revisions"]["dates"] = [elf_doc["creation_date"]]
            elf_doc["revisions"]["hashes"] = [machine_elf.revision]
            first_register = True

        revision_key = ut.legalize_key(machine_elf.revision)

        if store_source and (elf_doc["last_revision"] != machine_elf.revision or first_register) and (self.db["MachineElvesRevisions"]):
            revision_doc = self.db["MachineElvesRevisions"].createDocument()
            revision_doc["_key"] = revision_key
            revision_doc["source_code"] = machine_elf.source_code
            revision_doc["creation_date"] = now
            revision_doc.save()

        elf_doc["documentation"] = machine_elf.documentation
        elf_doc["last_revision"] = machine_elf.revision
        
        elf_doc.save()

    def get_job(self, job_id):
        return self.db["Jobs"][job_id]
    
    def get_result_id(self, job_id, name):
        return ut.legalize_key(job_id + name)

    def _save_job(self, job, now_date):
        job_key = ut.legalize_key(job.run_job_id)
        job_doc = self.db["Jobs"].createDocument()

        job_doc.set(
            {
            "_key": job_key,
            "task" : {
                    "name": job.task.name,
                    "signature": str(job.task.signature),
                    "source_code": job.task.source_code,
                    "documentation": job.task.documentation,
                    "revision": job.task.revision,
                },
                "machine_elf" : {
                    "id": job.worker_elf.uid,
                    "revision": job.worker_elf.revision,
                },
                "static_parameters": job.parameters.get_static_parameters(),
                "submit_date" : now_date,
                "start_date": None,
                "end_date": None,
                "status": custom_types.STATUS["PENDING"],
            }
        )
        job_doc.save()
        return job_doc

    def _save_parameters(self, job, job_doc, now_date):
        graph = self.db.graphs["Jobs_graph"]
        for name, return_placeholder in job.parameters.get_placeholder_parameters().items():
            result_key = self.get_result_id(return_placeholder.run_job_id, return_placeholder.name)
            data = {
                "name": name,
                "submit_date" : now_date,
                "result_id" : result_key,
                "completion_date": None,
                "status": custom_types.STATUS["PENDING"],
                "embedded": False,
                "embedding":{}
            }
            from_job = ut.legalize_key(return_placeholder.run_job_id)
            graph.link("Parameters", "Jobs/" + from_job, job_doc, data)

    def _save_embedded_parameters(self, job, job_doc, now_date):
        graph = self.db.graphs["Jobs_graph"]
        for parent_name, embed_placeholders in job.parameters.get_embedded_placeholder_parameters().items():
            for child_name, return_placeholder in embed_placeholders["placeholders"].items():
                result_key = self.get_result_id(return_placeholder.run_job_id, return_placeholder.name)
                data = {
                    "name": parent_name + "." + child_name,
                    "submit_date" : now_date,
                    "result_id" : result_key,
                    "completion_date": None,
                    "status": custom_types.STATUS["PENDING"],
                    "embedded": True,
                    "embedding":{
                        "parent_parameter_name": parent_name,
                        "self_name": child_name,
                        "embedding_function": embed_placeholders["emebedding_function"]
                    }
                }
                from_job = ut.legalize_key(return_placeholder.run_job_id)
                graph.link("Parameters", "Jobs/" + from_job, job_doc, data)

    def push_job(self, job):
        now = ut.gettime()
        job_doc = self._save_job(job, now)
        self._save_parameters(job, job_doc, now)
        self._save_embedded_parameters(job, job_doc, now)

    def get_received_jobs(self, elf_uid:str, all_jobs=False, status_restriction=[custom_types.STATUS["PENDING"]]):
        
        bind_vars = {"uid": elf_uid}
        
        if all_jobs:
            status_restriction = list(custom_types.STATUS.values())
        
        str_status_filter = []
        for status in status_restriction:
            pending = "job.status == @%s" % status
            str_status_filter.append(pending)
            bind_vars[status] = status

        if len(str_status_filter) > 0:
            str_status_filter = "FILTER " + " OR ".join(str_status_filter)
        else:
            str_status_filter = ""

        aql = """
            FOR job in Jobs
                FILTER job.machine_elf.id == @uid
                {str_status_filter}
                SORT job.creation_date DESC
                RETURN job
        """.format(str_status_filter=str_status_filter)

        ret_q = self.db.AQLQuery(aql, bindVars=bind_vars, batchSize=100, rawResults=True)
        ret = []
        for job in ret_q:
            job["id"] = job["_key"]
            ret.append(job)
        
        return ret

    def is_job_ready(self, job_id):
        job_doc = self.get_job(job_id)
        if job_doc["status"] not in [custom_types.STATUS["PENDING"], custom_types.STATUS["READY"]]:
            return False

        ready = 0
        count = 0
        for count, param in enumerate(self.db["Parameters"].fetchByExample({"_to": job_doc["_id"]}, batchSize=100)):
            count += 1
            if param["status"] is custom_types.STATUS["READY"]:
                ready += 1
        return count == ready

    def get_job_static_parameters(self, job_id):
        job_doc = self.get_job(job_id)
        return job_doc["static_parameters"].getStore()

    # def get_job_parameters_(self, job_id, embedded):
    #     """returns the list of available parameters for a job"""

    #     parameters = {}
    #     for param in self.db["Parameters"].fetchByExample({"_to": "Jobs/" + job_id, "embedded": embedded}, batchSize=100):
    #         try:
    #             value = self.db["Results"][param["result_id"]]
    #         except a_exc.DocumentNotFoundError:
    #             parameters[param["name"]] = custom_types.EmptyParameter
            
    #         else:
    #             parameters[param["name"]] = value["value"]
    #             if param["status"] != custom_types.STATUS["READY"]:
    #                 param["status"] = custom_types.STATUS["READY"]
    #                 param.save()

    #     return parameters

    def get_job_parameters(self, job_id, embedded):
        """returns the list of available parameters for a job"""

        aql = """
        FOR param in Parameters
            FILTER param._to == @job_id
            FILTER param.embedded == @embedded
            RETURN param
        """
        bind_vars = {"job_id": "Jobs/" +job_id, "embedded": embedded}
        query = self.db.AQLQuery(aql, bindVars=bind_vars, batchSize=1000)

        parameters = {}
        for param in query:
            try:
                value = self.db["Results"][param["result_id"]]
            except a_exc.DocumentNotFoundError:
                parameters[param["name"]] = custom_types.EmptyParameter
            else:
                if not embedded:
                    parameters[param["name"]] = value["value"]
                else:
                    parameters[param["name"]] = {
                        "value": value["value"],
                        "embedding": param["embedding"].getStore()
                    }
                if param["status"] != custom_types.STATUS["READY"]:
                    param["status"] = custom_types.STATUS["READY"]
                    param.save()

        return parameters

    def update_job_status(self, job_id, status):
        job_doc = self.get_job(job_id)
        job_doc["status"] = status
        job_doc.save()

    def start_job(self, job_id):
        job_doc = self.get_job(job_id)
        job_doc["status"] = custom_types.STATUS["RUNING"]
        job_doc["start_date"] = ut.gettime()
        job_doc.save()

    def complete_job(self, job_id):
        job_doc = self.get_job(job_id)
        job_doc["status"] = custom_types.STATUS["DONE"]
        job_doc["end_date"] = ut.gettime()
        job_doc.save()

    def register_job_failure(self, exc_type, exc_value, exc_traceback, job_id):
        import traceback
        import hashlib

        e = traceback.extract_tb(exc_traceback)
        now = ut.gettime()

        self.update_job_status(job_id, custom_types.STATUS["FAILED"])
        
        trace = traceback.extract_tb(exc_traceback).format()
        trace_str = "".join(trace).encode("utf-8")
        trace_key = ut.legalize_key( str( hashlib.sha256(trace_str).hexdigest() ) )

        try:
            failure_doc = self.db["Failures"][trace_key]
        except a_exc.DocumentNotFoundError:
            failure_doc = self.db["Failures"].createDocument()
            failure_doc.set(
                {
                    "_key": trace_key,
                    "type": str(exc_type),
                    "value": str(exc_value),
                    "traceback": trace,
                    "creation_date": now
                }
            )
            failure_doc.save()

        job_doc = self.get_job(job_id)
        graph = self.db.graphs["JobFailures_graph"]
        graph.link("JobFailures", job_doc, failure_doc, {"creation_date": now})
        job_doc["status"] = custom_types.STATUS["FAILED"]
        job_doc["end_date"] = ut.gettime()
        job_doc.save()

    def store_results(self, job_id, results:dict):
        if results is None:
            return
        
        if not type(results) is dict:
            raise  Exception("Results must be None or a dictionary")
        
        now = ut.gettime()

        # job_doc = self.get_job(job_id)

        for name, value in results.items():
            result_key = self.get_result_id(job_id, name)
            try:
                result_doc = self.db["Results"][result_key]
            except a_exc.DocumentNotFoundError:
                result_doc = self.db["Results"].createDocument()
        
            result_doc.set(
                {
                    "_key": result_key,
                    "value": value,
                    "creation_date": now,
                }
            )
            result_doc.save()
