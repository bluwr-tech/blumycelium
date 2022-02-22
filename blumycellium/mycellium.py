from icecream import ic
import uuid
import pyArango.theExceptions as a_exc
import utils as ut

import models as mod

import logging

logger = logging.getLogger("BLUMYCELLIUM")

class Mycellium:
    """docstring for Mycellium"""

    STATUS_PENDING=0
    STATUS_READY=1
    STATUS_DONE=2
    STATUS_FAILED=-1
    STATUS_UPSTREAM_FAILED=-2
    STATUS_EXPIRED=-3

    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
        self.db_name = "BLUMYC_" + name

        self.collections = mod.COLLECTIONS
        self.graphs = mod.GRAPHS

        print(self.db_name)
        if not self.connection.hasDatabase(self.db_name):
            logger.warning("Warining: Database %s does not exist. To create it run self.init with init_db=True" % self.db_name)
        else:
            self.db = self.connection[self.db_name]

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

    def init(self, init_db=False, users_to_create=None) :
        if init_db:
            self._init_db()

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

    def register_machine_elf(self, elf, store_source):
        import hashlib
        
        source = ut.inpsect_none_if_exception_or_empty(elf.__class__, "getsource")
        revision = str( elf.__class__.__name__ + hashlib.sha256(source.encode("utf-8")).hexdigest() )
        documentation = ut.inpsect_none_if_exception_or_empty(elf.__class__, "cleandoc")

        now = ut.gettime()
        first_register = False
        try:
            elf_doc = self.db["MachineElves"][elf.uid]
            elf_doc["revisions"]["dates"].append(now)
            elf_doc["revisions"]["dates"] = elf_doc["revisions"]["dates"]
            elf_doc["revisions"]["hashes"].append(revision)
            elf_doc["revisions"]["hashes"] = elf_doc["revisions"]["hashes"]
        except a_exc.DocumentNotFoundError:
            elf_doc = self.db["MachineElves"].createDocument()
            elf_doc["_key"] = elf.uid
            elf_doc["creation_date"] = now
            elf_doc["revisions"]["dates"] = [elf_doc["creation_date"]]
            elf_doc["revisions"]["hashes"] = [revision]
            first_register = True

        if store_source and (elf_doc["last_revision"] != revision or first_register):
            revision_doc = self.db["MachineElvesRevisions"].createDocument()
            revision_doc["_key"] = ut.legalize_key(revision)
            revision_doc["source_code"] = source
            revision_doc["creation_date"] = now
            revision_doc.save()

        elf_doc["documentation"] = documentation
        elf_doc["last_revision"] = revision
        
        elf_doc.save()

    def push_job(self, job):
        now = ut.gettime()
        graph = self.db.graphs["Jobs_graph"]
        # to_elf = self.db["MachineElves"][job.to_elf_uid]
        job_key = ut.legalize_key(job.run_id)
        job_doc = self.db["Jobs"].createDocument()
        job_doc.set(
            {
            "_key": job_key,
            "task" : {
                    "name": job.task.name,
                    "signature": job.task.signature,
                    "source_code": job.task.source_code,
                    "documentation": job.task.documentation,
                    "revision": job.task.revision,
                },
                "machine_elf" : {
                    "id": job.elf.uid,
                    "revision": job.elf.revision,
                },
                "static_parameters": job.parameters.get_static_parameters(),
                "submit_date" : now,
                "start_date": None,
                "completion_date": None,
                "status": self.STATUS_PENDING,
                
                "error_type": None,
                "error_traceback": None,
            }
        )
        job_doc.save()

        for name, return_placeholder in job.parameters.get_placeholder_parameters():
            result_id = "Results/" + return_placeholder.get_result_id(name)
            data = {
                "submit_date" : now,
                "result_id" : result_id,
                "completion_date": None,
                "status": self.STATUS_PENDING
            }
            graph.link("Jobs/" + return_placeholder.from_job_id, job_doc, data)
        
    def get_received_jobs(self, elf_uid):
        jobs = [ job["_key"] for job in self.db["Jobs"].fetchByExample({"to_elf_uid": "MachineElves/" + elf_uid}) ]
        return jobs

    def is_job_ready(self, job_id):
        ready = 0
        count = 0
        for count, param in enumerate(self.db["Parameters"].fetchByExample({"_to": "Jobs/" + job_id})):
            count += 1
            if param["status"] is self.STATUS_READY:
                ready += 1
        
        return count == ready

    def get_job_parameters(self, elf_uid):
        static_parameters = elf_doc["static_parameters"]
        parameters = {}
        for param in self.db["Parameters"].fetchByExample({"_to": elf_uid}):
            if param["status"] is self.STATUS_READY:
                parameters[param] = param["value"]
        
        elf_doc = self.db["MachineElves"][elf_uid]
        parameters.update(elf_doc["static_parameters"])
        return parameters

    def get_job_parameters(job):
        pass
    
    def update_job_status(self, *args, **kwargs):
        pass

    def get_jobs(self, *args, **kwargs):
        pass
