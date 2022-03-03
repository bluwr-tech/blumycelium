# from . import utils as ut
import utils as ut
from icecream import ic
ic.configureOutput(includeContext=True)

class ExecutionError(Exception):
    def __init__(self, code):
        msg="===\n{code}\n===".format(code=code)
        self.message = msg

class CodeBlock:
    def __init__(self, init_code=None, return_statement=None):
        self.init_code = init_code
        self.return_statement = return_statement

    def format(self, **string_kwargs):
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
    
    def __str__(self):
        return "*-CodeBlock %s-*" % (id(self))

    def __repr__(self):
        str_val="""%s\n%s""" % (self.init_code, self.return_statement)
        return str_val

class GraphParameter:

    def __init__(self, uid=None):
        if uid is None:
            uid = ut.get_random_variable_name()
        self.uid = uid
        self.value = None
        self.code_block = None
        self.dependencies = None
        self.dependency_values = {}
        
        self.computed_value = None

    def add_dependencies(self, *deps):
        if self.dependencies is None:
            self.dependencies = []

        dct = {dep.uid: dep for dep in deps}
        self.dependencies.append(dct)

    def make(self, visited_nodes=None, is_root=False):
        def _run_deps(visited):
            if self.dependencies:
                for batch in self.dependencies:
                    for dep in batch.values():
                        dep_ret = dep.make(visited)
                        if dep.uid in self.dependency_values:
                            self.dependency_values[dep.uid] = dep_ret
        
        if visited_nodes is None:
            visited_nodes = set()
        elif self.uid in visited_nodes:
            return self.computed_value

        if is_root:
             _run_deps(visited_nodes)

        if not self.value is None:
            self.computed_value = self.value
            visited_nodes.add(self.uid)
            return self.computed_value

        if not is_root:
            _run_deps(visited_nodes)

        self.computed_value = self.code_block.run(**self.dependency_values)
        visited_nodes.add(self.uid)
        return self.computed_value

    def traverse(self, visited_nodes=None, is_root=True, root_uid=None):
        from rich.tree import Tree
        from rich import print

        def _run_deps(visited, tree, tree_root_uid):
            if self.dependencies:
                for batch in self.dependencies:
                    for dep in batch.values():
                        tree.add(dep.traverse(visited, False, tree_root_uid))
                        # print(tree)

        if is_root or root_uid == self.uid:
            tree = Tree("[blue]%s" % repr(self))
        else:
            tree = Tree("%s" % repr(self))
        
        if visited_nodes is None:
            visited_nodes = set()
        elif self.uid in visited_nodes:
            if self.uid != root_uid:
                tree = Tree("[red]%s" % repr(self))
            return tree

        if is_root:
            root_uid = self.uid
            _run_deps(visited_nodes, tree, root_uid)

        if not self.value is None:
            visited_nodes.add(self.uid)
            return tree

        if not is_root:
            _run_deps(visited_nodes, tree, root_uid)

        visited_nodes.add(self.uid)
        return tree

    def pp_traverse(self):
        import json
        trav = self.traverse()

        print(json.dumps(trav, indent=4).replace(" ", "-"))

    def set_value(self, value):
        if self.code_block is not None or self.dependencies is not None:
            raise Exception("A code block has been defined, you can either set a value or a code block")
        self.value = value

    def set_code_block(self, init_code, return_statement, **dependencies):
        if self.value is not None:
            raise Exception("A code block has been defined, you can either set a value or a code block")

        string_kwargs = {}
        for hr_name, dep in dependencies.items():
            self.dependency_values[dep.uid] = None
            if not isinstance(dep, GraphParameter):
                raise Exception("All depenedencies must be GraphParameters, got: '%s'" % type(dep))
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
        return "*-GraphParameter '%s' value:'%s' code_block:'%s' dependencies:'%s' -*" % (self.uid, self.value, self.code_block, deps)

    def __repr__(self):
        deps = 0
        if self.dependencies is not None:
            for batch in self.dependencies:
                for dep in batch.values():
                    deps += 1 
        return "*-GraphParameter '%s' value:'%s' code_block:'%s' dependencies:'%s' -*" % (self.uid, self.value, self.code_block, deps)

def unravel_list(lst):
    last_list_param = GraphParameter()
    last_list_param.set_value([])

    params = [last_list_param]
    for value in lst:
        val_param = GraphParameter()
        val_param.set_value(value)

        new_list_param = GraphParameter()
        
        init_code="""
        def add(lst, value):
            lst.append(value)
            return lst""".strip()
        return_statement = "add({list_var}, {value_var})"
        
        new_list_param.set_code_block(
            init_code=init_code,
            return_statement=return_statement,
            list_var=last_list_param,
            value_var=val_param
            )
        
        last_list_param = new_list_param
        params.append(val_param)
        params.append(last_list_param)
    return params

def unravel_dict(dct):
    last_list_param = GraphParameter()
    last_list_param.set_value({})

    params = [last_list_param]
    for key, value in dct.items():
        val_param = GraphParameter()
        val_param.set_value(value)

        new_list_param = GraphParameter()
        
        init_code="""
        def add(dct, key, value):
            dct[key]=value
            return dct""".strip()
        return_statement = "add({list_var}, %s, {value_var})" % key
        
        new_list_param.set_code_block(
            init_code=init_code,
            return_statement=return_statement,
            list_var=last_list_param,
            value_var=val_param
            )
        
        last_list_param = new_list_param
        params.append(val_param)
        params.append(last_list_param)
    return params

class Value(object):
    
    def _init(self, as_type=None, parent=None):
        super(Value, self).__init__()
        self.parameter = GraphParameter()
        self.as_type = as_type
        self.parent = parent
        self.closed_init = False

    def close_init(self):
        self.closed_init = True

    def __init__(self, *args, **kwargs):
        self._init(*args, **kwargs)
        self.close_init()

    def set_value(self, *args, **kwargs):
        return self.parameter.set_value(*args, **kwargs)

    def set_code_block(self, *args, **kwargs):
        return self.parameter.set_code_block(*args, **kwargs)

    def _get_parameter(self, param):
        if isinstance(param, Value):
            return params.parameter
        elif isinstance(param, GraphParameter):
            return param

        new_param = GraphParameter()
        if type(param) is str:
            param = param
        new_param.set_value(param)
        return new_param

    def _validate_type(self, key):
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

        code = "{self_param}[{key}]={value}"
        
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

    def make(self):
        return self.parameter.make(is_root=True)

    def __str__(self):
        return "Value: %s" % str(self.parameter)

    def __repr__(self):
        return "Value: %s" % repr(self.parameter)

def test_unravels():
    lst = [1, 2, 3, 4, 5, 10]
    res = unravel_list(lst)
    print(res[-1].make())

    res = unravel_dict(dct)
    print(res[-1].make())

def test_subslist():
    lst = [1, 2, 3, 4, 5, 10]
    param = GraphParameter()
    param.set_value(lst)

    sub = param[1:-1]
    ic(sub)
    ic(sub.make())

def test_getitem():
    dct = {1: 1, 2: 2, 3: 3}

    param = Value()
    param.set_value(dct)

    sub = param[1]
    ic(sub)
    ic(sub.make())

def test_setitem():
    dct = {1: 1, 2: 2, 3: 3}
    param = Value()
    param.set_value(dct)

    param[1]=100
    ic(param)
    ic(param.make())

def test_arbitrary():
    lst = [1, 2, 3, 4, 5]
    param = Value()
    param.set_value(lst)

    param.extend(lst)
    
    param.append(60)
    param.append(61)
    param.pop()
    ic(param.make())

def test_easy_unravel():
    from rich import print

    lst = [1, 2, 3, 4, 5]
    param = Value()
    param.set_value([])

    for v in lst:
        param.append(v)
    
    tree = param.parameter.traverse()
    
    print(tree)
    ic(param.make())

if __name__ == '__main__':
    test_easy_unravel()
