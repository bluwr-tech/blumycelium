def inpsect_none_if_exception_or_empty(obj_to_inspect, inspect_fct):
    """runs an inspect function on obj_to_inspect and returns None if the result is empty or returns an exception"""
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

def legalize_key(key):
    """returns a string that can serve as a valid arangodb _key"""
    import re
    key = key.lower().replace(" ", "_")

    pattern = re.compile('[\W]+') 
    key = pattern.sub('', key) 

    return key
