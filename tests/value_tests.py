from blumycelium.graph_parameters import *

import unittest

class ValueTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_subslist(self):
        lst = [1, 2, 3, 4, 5, 10]
        param = Value()
        param.set_value(lst)

        sub = param[1:-1]
        # ic(sub)
        # ic(sub.make())
        self.assertEqual(lst[1:-1], sub.make())

    def test_getitem_dct(self):
        dct = {1: 1, 2: 2, 3: 3}

        param = Value()
        param.set_value(dct)

        for key in dct.keys():
            sub = param[key]
            self.assertEqual(dct[key], sub.make())

    def test_getitem_lst(self):
        lst = [1, 2, 3, 4, 5, 10]

        param = Value()
        param.set_value(lst)

        for key in range(len(lst)):
            sub = param[key]
            self.assertEqual(lst[key], sub.make())

    def test_setitem_dct(self):
        dct = {1: 1, 2: 2, 3: 3}
        dct2 = {1: 10, 2: 20, 3: 30}
        param = Value()
        param.set_value(dct)

        for key in dct:
            param[key]=dct2[key]
    
        dct_final = param.make()
        self.assertEqual(dct_final, dct2)

    def test_setitem_lst(self):
        lst = list(range(10))
        lst2 = list(range(100, 110))
        param = Value()
        param.set_value(lst)

        for key in range(len(lst)):
            param[key]=lst2[key]
    
        lst_final = param.make()
        self.assertEqual(lst_final, lst2)

    def test_arbitrary_functions_lst(self):
        """apply an arbitrary set of function to a list parameter"""
        lst = [1, 2, 3, 4, 5]
        lst2 = list(lst)

        param = Value()
        param.set_value(lst)

        param.extend(lst)
        lst2.extend(lst)

        param.append(60)
        lst2.append(60)
        param.append(61)
        lst2.append(61)
        param.pop()
        lst2.pop()

        self.assertEqual(lst2, param.make())

    def test_arbitrary_functions_dct(self):
        """apply an arbitrary set of function to a list parameter"""
        dct = {1: 1, 2: 2, 3: 3}
        dct2 = dict(dct)

        param = Value()
        param.set_value(dct)

        tmp_dct = {"a": "abc"}
        param.update(tmp_dct)
        dct2.update(tmp_dct)

        del param[1]
        del dct2[1]
        
        self.assertEqual(dct2, param.make())

    # def test_easy_unravel():
    #     from rich import print

    #     lst = [1, 2, 3, 4, 5]
    #     param = Value()
    #     param.set_value([])

    #     for v in lst:
    #         param.append(v)
            
    #     ic(param.make())

if __name__ == '__main__':
    unittest.main()

if False:
    # def test_subslist():
    #     lst = [1, 2, 3, 4, 5, 10]
    #     param = Value()
    #     param.set_value(lst)

    #     sub = param[1:-1]
    #     ic(sub)
    #     ic(sub.make())

    # def test_getitem():
    #     dct = {1: 1, 2: 2, 3: 3}

    #     param = Value()
    #     param.set_value(dct)

    #     sub = param[1]
    #     ic(sub)
    #     ic(sub.make())

    # def test_setitem():
    #     dct = {1: 1, 2: 2, 3: 3}
    #     param = Value()
    #     param.set_value(dct)

    #     param[1]=100
    #     ic(param)
    #     ic(param.make())

    # def test_arbitrary():
    #     lst = [1, 2, 3, 4, 5]
    #     param = Value()
    #     param.set_value(lst)

    #     param.extend(lst)
        
    #     param.append(60)
    #     param.append(61)
    #     param.pop()
    #     ic(param.make())

    # def test_easy_unravel():
    #     from rich import print

    #     lst = [1, 2, 3, 4, 5]
    #     param = Value()
    #     param.set_value([])

    #     for v in lst:
    #         param.append(v)
            
    #     ic(param.make())

    def test_nested_unravel_traversal():
        from rich import print

        lst = [1, 2, 3, 4, 5]
        param = Value()
        param.set_value([])

        for v in lst:
            param.append(v)

        val = Value()
        val.set_value([1])
        val.append(100)

        val2 = Value()
        val2.set_value([2])
        val2.append(200)

        val.append(val2)
        # val.pp_traverse(representation_attributes=None)
        param.append(val)
            
        param.pp_traverse(representation_attributes=None)
        print(param.to_dict(reccursive=True))
        ic(param.make())


    def test_rebuild_from_traversal():
        from rich import print

        lst = [1, 2, 3, 4, 5]
        param = Value()
        param.set_value([])

        for v in lst:
            param.append(v)
            
        param.pp_traverse(representation_attributes=["value", "code_block", "uid", "python_id"])
        print("=====")
        trav = param.traverse()
        # print(trav)

        param2 = GraphParameter.build_from_traversal(trav)
        param2.pp_traverse(representation_attributes=["value", "code_block", "uid", "python_id"])

        ic(param.make())
        ic(param2.make())


    # test_subslist()
    # test_getitem()
    # test_setitem()
    # test_arbitrary()
    # test_easy_unravel()   