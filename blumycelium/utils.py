def inpsect_none_if_exception_or_empty(obj_to_inspect, inspect_fct_name):
    """runs an inspect function on obj_to_inspect and returns None if the result is empty or returns an exception"""
    import inspect

    inspect_fct = getattr(inspect, inspect_fct_name)
    ret = None
    try:
        ret = inspect_fct(obj_to_inspect)
        if len(ret) == 0: ret = None
    except Exception as e:
        pass

    return ret

def gettime():
    """return timestamp"""
    import time
    return time.time()

def get_hash_key(to_hash:str, prefix=None, suffix=None):
    """return a hash of to_hash that can serve as a key"""

    import hashlib
    if prefix is None:
        prefix = ""

    if suffix is None:
        suffix = ""

    val =  prefix + str(hashlib.sha256(to_hash.encode("utf-8")).hexdigest()) + suffix
    return legalize_key( val )

def legalize_key(key):
    """returns a string that can serve as a valid key for database"""
    import re
    key = key.lower().replace(" ", "_")

    pattern = re.compile('[\W]+') 
    key = pattern.sub('', key) 

    return key

def getuid():
    """returns a random id that can serve as a key"""
    import uuid
    val = str(uuid.uuid4())
    return legalize_key(val)

def get_random_variable_name():
    """returns a string that can serve as a python variable name"""
    import uuid
    val = str(uuid.uuid4())
    return "var_" + legalize_key(val)