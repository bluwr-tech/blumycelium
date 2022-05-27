from . import utils as ut
# import utils as ut
from icecream import ic
ic.configureOutput(includeContext=True)

class ExecutionError(Exception):
    def __init__(self, code):
        msg="===\n{code}\n===".format(code=code)
        self.message = msg

class CodeBlock:
    """a code block of python code to run"""
    def __init__(self, init_code=None, return_statement=None):
        self.init_code = init_code
        self.return_statement = return_statement

    def format(self, **string_kwargs):
        """replace the name of variables by their myc_back_variables references"""
        import re
        def _sub_var_names(code):
            ret = re.sub("(var_[^\W]+)", r"myc_back_variables['\1']", code)
            return ret

        if not self.init_code is None:
            self.init_code = self.init_code.format(**string_kwargs)
            self.init_code = _sub_var_names(self.init_code)
        if not self.return_statement is None:
            self.return_statement = self.return_statement.format(**string_kwargs)
            self.return_statement =_sub_var_names(self.return_statement)

    def run(self, **myc_back_variables):
        """run the code block"""
        if not self.init_code is None:
            try:
                exec(self.init_code)
            except:
                raise ExecutionError(self.init_code)

        if not self.return_statement is None:
            try:
                return eval(self.return_statement) 
            except:
                raise ExecutionError(self.return_statement)
    
    def to_dict(self):
        """return a dictionary version of the code block"""
        return {
            "init_code": self.init_code,
            "return_statement": self.return_statement
        }

    def __str__(self):
        return "*-CodeBlock %s-*" % (id(self))

    def __repr__(self):
        str_val="""%s\n%s""" % (self.init_code, self.return_statement)
        return str_val

class GraphParameter:
    """A graph of Parameters"""
    def __init__(self, uid=None):
        if uid is None:
            uid = ut.get_random_variable_name()
        self.python_id = id(self)
        self.uid = uid
        self.value = None
        self.code_block = None
        self.dependencies = None
        self.dependency_values = {}
        
        self.computed_value = None
        
        self.origin = None
        self.pull_origin_function = None

    def set_origin(self, uid, pull_origin_function=None):
        """set the origin (address) of the parameter and function to retreive the value from the origin"""
        self.origin = uid
        self.pull_origin_function = pull_origin_function
        # ic(self, self.origin, self.pull_origin_function)

    def set_pull_origin_function(self, fct):
        """set the function to pull jvalue form the origin"""
        self.pull_origin_function = fct

    def _dict_representation(self):
        """return a dcitionnary representation of the paramater"""
        ret = {
            "uid": self.uid,
            "value": self.value,
            "code_block": self.code_block,
            "origin": self.origin
        }
        
        return ret

    def to_dict(self, reccursive=False, visited_nodes=None, copy_values=True):
        """return a dict representation of the parameter recursively if asked to"""
        import copy

        if visited_nodes is None:
            visited_nodes = set()

        value = self.value
        if copy_values:
            value = copy.copy(value)

        ret = self._dict_representation()
        
        if not self.code_block is None:
            ret["code_block"] = self.code_block.to_dict()

        if reccursive and not (self.uid in visited_nodes):
            visited_nodes.add(self.uid)
            ret["dependencies"] = {}
            if self.dependencies is not None:
                for batch in self.dependencies:
                    for uid, dep in batch.items():
                        ret["dependencies"][uid] = dep.to_dict(reccursive=True, visited_nodes=visited_nodes)
        return ret

    def add_dependencies(self, *deps):
        """add dependencies (other GraphParaemters) needed to compute the value"""
        if self.dependencies is None:
            self.dependencies = []

        if len(deps) > 0:
            dct = {dep.uid: dep for dep in deps}
            self.dependencies.append(dct)
            for duid in dct:
                self.dependency_values[duid] = None

    def make(self, visited_nodes=None, is_root=False):
        """compute the value of the paraneter and return it"""
        def _run_deps(visited):
            if self.dependencies:
                for batch in self.dependencies:
                    for dep in batch.values():
                        dep_ret = dep.make(visited)
                        if dep.uid in self.dependency_values:
                            self.dependency_values[dep.uid] = dep_ret
        
        if not self.value is None:
            self.computed_value = self.value
               
        if visited_nodes is None:
            visited_nodes = set()
        
        if self.uid in visited_nodes:
            return self.computed_value

        visited_nodes.add(self.uid)
        _run_deps(visited_nodes)

        if self.value is None:
            if not self.code_block is None:
                self.computed_value = self.code_block.run(**self.dependency_values)
            elif (not self.pull_origin_function is None ) and (not self.origin is None):
                self.computed_value = self.pull_origin_function(self.origin)
            else:
                raise ValueDerivationError("Unable to retrieve value. No defined value, code_block or origin function")
        return self.computed_value

    def traverse(self, visited_nodes=None, is_root=True, root_uid=None, to_dict=True):
        """traverse the graph dependency tree and return a dictionary representing it"""
        def _add_tree(node, is_root, root_uid, visited, as_dict):
            nnn = node
            if as_dict:
                nnn = node.to_dict()
            return {"node": nnn, "uid": node.uid, "is_root": is_root, "root_uid": root_uid, "visited": visited, "dependencies": {}}

        def _run_deps(visited, tree, tree_root_uid, as_dict):
            if self.dependencies:
                for batch in self.dependencies:
                    for dep in batch.values():
                        tree["dependencies"][dep.uid] = dep.traverse(visited_nodes=visited, is_root=False, root_uid=tree_root_uid, to_dict=as_dict)
        
        if visited_nodes is None:
            visited_nodes = set()

        if is_root:
            root_uid = self.uid

        tree = _add_tree(self, root_uid==self.uid, root_uid, self.uid in visited_nodes, as_dict=to_dict)
        
        if self.uid in visited_nodes:
            return tree

        visited_nodes.add(self.uid)
        _run_deps(visited_nodes, tree, root_uid, as_dict=to_dict)

        return tree

    @classmethod
    def build_from_traversal(cls, trav:dict, pull_origin_function=None):
        """build a parameter from a traversal dictionary"""
        def _build_node(dct_node):
            node = GraphParameter(uid=dct_node["uid"])
            node.value = dct_node["value"]
            if not dct_node["code_block"] is None:
                code_block = CodeBlock(init_code=dct_node["code_block"]["init_code"], return_statement=dct_node["code_block"]["return_statement"])
                node.code_block = code_block
            if not dct_node["origin"] is None:
                node.set_origin(dct_node["origin"])
                node.set_pull_origin_function(pull_origin_function)
            return node

        def _get_node(dct, all_nodes_dct):
            try:
                return all_nodes_dct[dct["uid"]]
            except KeyError:
                node = _build_node(dct)
                all_nodes_dct[node.uid] = node
                return node

        def _rec_build(dct, all_nodes_dct):
            if all_nodes_dct is None:
                all_nodes_dct = {}

            root_node = _get_node(dct["node"], all_nodes_dct)
            deps = []
            for dep_dct in dct["dependencies"].values():
                dep_node = _get_node(dep_dct["node"], all_nodes_dct)
                deps.append(dep_node)
                if not dct["visited"]:
                    _rec_build(dep_dct, all_nodes_dct)
            root_node.add_dependencies(*deps)
            return all_nodes_dct
        
        nodes = _rec_build(trav, None)
        root = nodes[trav["uid"]]
    
        return root

    def pp_traverse(self, full_representation=False, representation_attributes=["value", "code_block"], print_it=True):
        """a pretty print of the graph representation with dependencies"""
        from rich.tree import Tree
        from rich import print

        def _get_represenation(node):
            if full_representation:
                return str(node)
            elif representation_attributes and len(representation_attributes) > 0:
                vals = [ "%s: %s" % (attr, str( getattr(node, attr)) ) for attr in representation_attributes if not getattr(node, attr) is None]
                return ", ".join(vals)
            return repr(node)
            
        def _get_node(node):
            if node["is_root"]:
                tree = Tree("[bold blue]>ROOT: %s" % _get_represenation(node["node"]))
            elif node['visited']:
                tree = Tree("[bold magenta]>ALREADY VISITED: %s" % _get_represenation(node["node"]))
            else:
                tree = Tree("%s" % _get_represenation(node["node"]))
            return tree
        
        def _traverse(trav, curr_tree):
            for branch in trav["dependencies"].values():
                node = _get_node(branch)
                curr_tree.add(node)
                _traverse(branch, node)
            return tree

        trav = self.traverse(to_dict=False)
        tree = _get_node(trav)
        tree = _traverse(trav, tree)

        if print_it:
            print(tree)
    
        return tree

    def set_value(self, value):
        """set the static value of the parameter"""
        if not (self.code_block is None and self.origin is None) :
            raise MultipleDerivationError("Can either have a code block, a value or an origin")
        self.value = value

    def set_code_block(self, init_code, return_statement, **dependencies):
        """set the code block of the parameter"""
        if not (self.value is None and self.origin is None) :
            raise MultipleDerivationError("Can either have a code block, a value or an origin")

        string_kwargs = {}
        for hr_name, dep in dependencies.items():
            self.dependency_values[dep.uid] = None
            if not isinstance(dep, GraphParameter):
                raise DependencyTypeError("All depenedencies must be GraphParameters, got: '%s'" % type(dep))
            string_kwargs[hr_name] = dep.uid 

        if self.dependencies is None:
            self.dependencies = []
        self.dependencies.append(dependencies)
        
        
        self.code_block = CodeBlock(init_code, return_statement)
        self.code_block.format(**string_kwargs)

    def __str__(self):
        if self.dependencies is not None:
            deps = []
            for batch in self.dependencies:
                for dep in batch.values():
                    deps.append(dep.uid)
        else:
            deps = None
        return "*-GraphParameter '%s' value:'%s' code_block:'%s' origin:'%s' dependencies:'%s' -*" % (self.uid, self.value, self.code_block, self.origin, deps)

    def __repr__(self):
        deps = 0
        if self.dependencies is not None:
            for batch in self.dependencies:
                for dep in batch.values():
                    deps += 1 
        return "*-GraphParameter '%s' value:'%s' code_block:'%s' origin:'%s' dependencies:'%s' -*" % (self.uid, self.value, self.code_block, self.origin, deps)

class Value(object):
    """A wrapper for a graph parameter"""
    def _init(self, as_type=None, parent=None):
        super(Value, self).__init__()
        self.parameter = GraphParameter()
        self.as_type = as_type
        self.parent = parent
        # self.closed_init = False
        self.dependencies = []
        self.made_value = None

    # def close_init(self):
        # self.closed_init = True

    def __init__(self, *args, **kwargs):
        self._init(*args, **kwargs)
        # self.close_init()

    def set_value(self, value):
        """set the static value"""
        self.as_type = type(value)
        return self.parameter.set_value(value)

    def set_code_block(self, *args, **kwargs):
        """set the code block to run"""
        return self.parameter.set_code_block(*args, **kwargs)

    def traverse(self, *args, **kwargs):
        """return a dictionary representing the value and it's dependencies"""
        return self.parameter.traverse(*args, **kwargs)

    def to_dict(self, *args, **kwargs):
        """return a dictionary representing the value"""
        return self.parameter.to_dict( *args, **kwargs)

    def pp_traverse(self, *args, **kwargs):
        """pretty print the value and it's dependencies"""
        return self.parameter.pp_traverse(*args, **kwargs)

    def _get_parameter(self, param):
        """return a GraphParameter"""
        if isinstance(param, Value):
            # self.parent.dependencies.append(param)
            self.parent.parameter.add_dependencies(param.parameter)
            return param.parameter
        elif isinstance(param, GraphParameter):
            self.parent.dependencies.append(param)
            self.parent.parameter.add_dependencies(param)
            return param

        new_param = GraphParameter()
        if type(param) is str:
            param = param
        new_param.set_value(param)
        return new_param

    def _validate_type(self, key):
        """is as_type is defined validate that the object specified in 'as_type' has an attribute named 'key'"""
        as_type = object.__getattribute__(self, "as_type")
        if not as_type is None:
            getattr(as_type, key) #will raise an exception if the attribute is non-existant

    def __getitem__(self, key):
        self._validate_type("__getitem__")

        code = "{self_param}[{key}]"
        key_param = GraphParameter()
        key_param.set_value(key)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, key=key_param)
        return new_param

    def __setitem__(self, key, value):
        self._validate_type("__setitem__")

        init_code="""
        def add(dct, key, value):
            dct[key]=value
            return dct""".strip()
        return_statement = "add({self_param}, {key}, {value})"
       
        key_param = self._get_parameter(key)
        value_param = self._get_parameter(value)
        
        new_param = GraphParameter()
        new_param.set_code_block(init_code=init_code, return_statement=return_statement, self_param=self.parameter, key=key_param, value=value_param)
        self.parameter = new_param

    # def __setattr__(self, key, value):
    #     # ic(key, value)
    #     try:
    #         closed_init = object.__getattribute__(self, "closed_init")
    #     except AttributeError:
    #         closed_init = False

    #     if not closed_init:
    #         return object.__setattr__(self, key, value)
    #     else:        
    #         init_code="""
    #         def add(obj, key, value):
    #             setattr(obj, key, value)
    #             return obj""".strip()
    #         return_statement = "add({self_param}, {key}, {value})"

    #         code = "{self_param}[{key}]={value}"
            
    #         key_param = self._get_parameter(key)
    #         value_param = self._get_parameter(value)
            
    #         new_param = GraphParameter()
    #         new_param.set_code_block(init_code=init_code, return_statement=return_statement, self_param=self.parameter, key=key_param, value=value_param)
            
    #         self.parameter = new_param

    def __getattr__(self, key):
        _validate_type = object.__getattribute__(self, "_validate_type")
        _validate_type(key)

        self_param = object.__getattribute__(self, "parameter")
        key_param = object.__getattribute__(self, "_get_parameter")(key)

        return_statement = "getattr({self_param}, {key})"

        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=return_statement, self_param=self_param, key=key_param)
        
        new_value = Value(parent=self)
        new_value.parameter = new_param
        return new_value

    def __call__(self, *args, **kwargs):
        def _populate(iterator, f_params, f_map, with_equals):
            for key, value in iterator:
                name = "{val_%s}" % key 
                
                if with_equals:
                    final_params.append( "%s=" % key + name)
                else:
                    final_params.append(name)
                
                final_params_map[name[1:-1]] = self._get_parameter(value)
            
            return f_params, f_map

        
        final_params = []
        final_params_map = {}
        final_params, final_params_map = _populate(enumerate(args), final_params, final_params_map, False)
        final_params, final_params_map = _populate(kwargs.items(), final_params, final_params_map, True)

        final_params = ", ".join(final_params)

        return_statement = "{self_param}(%s)" % (final_params)
        
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=return_statement, self_param=self.parameter, **final_params_map)
        
        if not self.parent is None:
            self.parent.parameter.add_dependencies(new_param)
        self.parameter = new_param

        return self

    def make(self, force=False):
        """compute a return the value represented by the Value object"""
        if self.made_value is None or force :
            self.made_value = self.parameter.make(is_root=True)
        return self.made_value

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, str(self.parameter))

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, repr(self.parameter))

    def __mul__(self, value):
        self._validate_type("__mul__")

        code = "{self_param} * {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

    def __add__(self, value):
        self._validate_type("__add__")

        code = "{self_param} + {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

    def __sub__(self, value):
        self._validate_type("__sub__")

        code = "{self_param} - {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

    def __div__(self, value):
        self._validate_type("__div__")

        code = "{self_param} / {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

    def __contain__(self, value):
        self._validate_type("__contain__")

        code = "{self_param} in {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

    def __equals__(self, value):
        self._validate_type("__equals__")

        code = "{self_param} == {value}"
        value_param = GraphParameter()
        value_param.set_value(value)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, value=value_param)
        return new_param

def unravel_list(lst):
    param = Value()
    param.set_value([])
    for val in lst:
        if type(val) in (list, tuple, set):
            val = unravel_list(val)
        elif type(val) is dict:
            val = unravel_dict(val)
        param.append(val)
    return param

def unravel_dict(dct):
    param = Value()
    param.set_value({})
    for key, val in dct.items():
        if type(val) in (list, tuple, set):
            val = unravel_list(val)
        elif type(val) is dict:
            val = unravel_dict(val)
        param[key] = val
    return param

def unravel(obj):
    if type(obj) in (list, tuple, set):
        return unravel_list(obj)
    elif type(obj) is dict:
        return unravel_dict(obj)
    else:
        raise TypeError("Wrong type: '%s', except list or dict" % type(obj))
