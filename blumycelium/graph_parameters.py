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

    def make(self):
        if not self.value is None:
            return self.value

        for dep in self.dependencies.values():
            self.dependency_values[dep.uid] = dep.make()

        ret = self.code_block.run(**self.dependency_values)
        return ret

    def set_value(self, value):
        if self.code_block is not None or self.dependencies is not None:
            raise Exception("A code block has been defined, you can either set a value or a code block")
        self.value = value

    def set_code_block(self, init_code, return_statement, **dependencies):
        if self.value is not None:
            raise Exception("A code block has been defined, you can either set a value or a code block")
        self.code_block = CodeBlock(init_code, return_statement)
        self.dependencies = dependencies
        
        string_kwargs = {}
        for hr_name, dep in self.dependencies.items():
            if not isinstance(dep, GraphParameter):
                raise Exception("All depenedencies must be GraphParameters, got: '%s'" % type(dep))
            string_kwargs[hr_name] = dep.uid 
        
        self.code_block.format(**string_kwargs)

    def __str__(self):
        if self.dependencies is not None:
            deps = [ dep.uid for dep in self.dependencies.values() ]
        else:
            deps = None
        return "*-GraphParameter '%s' value:'%s' code_block:'%s' dependencies:'%s' -*" % (self.uid, self.value, self.code_block, deps)

    def __repr__(self):
        return str(self)

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
    def __init__(self, as_type=None):
        super(Value, self).__init__()
        self.parameter = GraphParameter()
        self.as_type = as_type

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

    def __getitem__(self, key):
        code = "{self_param}[{key}]"
        key_param = GraphParameter()
        key_param.set_value(key)
        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=code, self_param=self.parameter, key=key_param)
        return new_param

    def __setitem__(self, key, value):
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

    def __getattr__(self, key):
        self_param = object.__getattribute__(self, "parameter")
        key_param = object.__getattribute__(self, "_get_parameter")(key)

        return_statement = "getattr({self_param}, {key})"

        new_param = GraphParameter()
        new_param.set_code_block(init_code=None, return_statement=return_statement, self_param=self_param, key=key_param)
        
        new_value = Value()
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
        self.parameter = new_param
        return self

    def make(self):
        return self.parameter.make()

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

    ic(param)
    h = param.append(60)
    ic(h)
    ic(h.make())
    ic(param.make())
    # ic(param.append(60).make())
    # ic(param)

if __name__ == '__main__':
    test_arbitrary()
