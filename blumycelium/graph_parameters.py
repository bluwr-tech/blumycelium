import utils as ut
from icecream import ic
ic.configureOutput(includeContext=True)

class CodeBlock:
    def __init__(self, init_code=None, return_statement=None):
        self.init_code = init_code
        self.return_statement = return_statement

    def format(self, **string_kwargs):
        if self.init_code is not None:
            self.init_code = self.init_code.format(**string_kwargs)
        if self.return_statement is not None:
            self.return_statement = self.return_statement.format(**string_kwargs)

    def run(self, **variable_setup):
        variables_init = [ "%s=%s" % (var, value) for var, value in variable_setup.items() ]
        if len(variables_init) > 0:
            variables_init = "\n".join(variables_init)
            exec(variables_init)

        if self.init_code is not None:
            exec(self.init_code)
        if self.return_statement is not None:
            return eval(self.return_statement) 

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
        if self.value is not None:
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
                raise Exception("All depenedencies must be GraphParameters")
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
        def append(lst, value):
            lst.append(value)
            return lst""".strip()
        return_statement = "append({list_var}, {value_var})"
        
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


if __name__ == '__main__':
    lst = [1, 2, 3, 4, 5, 10]
    res = unravel_list(lst)
    ic(res[-1], res[-1].code_block)
    ic(res[-1].make())