class Task:
    """docstring for Task"""
    def __init__(self, name, arguments):
        super(Task, self).__init__()
        self.name = name

    def _find_relevant_taks(self):
        """load all tasks wit hthe right name and find one with the right arguments"""
        pass

    def _test_task_relevance(self):
        """test if the task supports the given arguments"""
        pass

class Job:
    """docstring for Job"""
    def __init__(self, arg):
        super(Job, self).__init__()
        self.arg = arg

    def _start(self):
        """registers the job"""
        pass

    def _end(self):
        """exit the jb and save the results"""
        pass

    def _run(self):
        """runs the job"""
        pass

if False:
    myc.push(
        from_="bluwr",
        to_="deleter",
        action= "delete_account",
        unique_handel=unique_handle,
        arguments={
            userid: "Users/xxx"
        }
    )
    myc.push(
        from_="deleter",
        to_="bluwr",
        action= "delete_account",
        unique_handel=unique_handle
    )
