from keops.python_engine.map_reduce import *
from ctypes import c_int, CDLL


class create_or_load:
    library = {}
    @staticmethod
    def __call__(cls, *args):
        cls_id = str(cls)
        if cls_id not in create_or_load.library:
            create_or_load.library[cls_id] = {}
        cls_library = create_or_load.library[cls_id]
        hash_name = get_hash_name(*args)
        if hash_name in cls_library:
            return cls_library[hash_name]
        else:
            obj = cls(*args)
            cls_library[hash_name] = obj
            return obj
            


class get_keops_routine_class:
    
    def __init__(self, map_reduce_id, *args):
        self.dll = None
        map_reduce_class = eval(map_reduce_id)
        self.map_reduce_obj = map_reduce_class(*args)
        
        # detecting the case of formula being equal to zero, to bypass reduction.
        rf = self.map_reduce_obj.red_formula
        if isinstance(rf, Zero_Reduction) or (isinstance(rf.formula, Zero) and isinstance(rf, Sum_Reduction)):
            self.map_reduce_obj = map_reduce_class.AssignZero(*args)
                 
        self.load_dll()
            
    def load_dll(self):
        res = self.map_reduce_obj.get_dll_and_params()
        self.dllname = res["dllname"]
        self.dll = CDLL(self.dllname)            
        self.tagI = res["tagI"]
        self.dim = res["dim"]
        return self
        
    def __call__(self, nx, ny, device_id, ranges_ctype, out_ctype, *args_ctype):
        if self.dll is not None:
            self.dll.launch_keops.argtypes = [c_int, c_int, c_int, ranges_ctype["type"], out_ctype["type"]] + [arg["type"] for arg in args_ctype]
            c_args = [arg["data"] for arg in args_ctype]
            self.dll.launch_keops(c_int(nx), c_int(ny), c_int(device_id), ranges_ctype["data"], out_ctype["data"], *c_args)   
   
            
def get_keops_routine(*args):
    return create_or_load()(get_keops_routine_class, *args)