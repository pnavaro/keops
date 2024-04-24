from .c_instruction import c_instruction, c_empty_instruction
from .c_lvalue import c_lvalue
from .c_expression import c_expression, c_pointer, py2c
from .c_for import c_for_loop
from .c_variable import c_variable
from .misc import Meta_Toolbox_Error, new_c_name


class c_array:
    def __init__(self, dtype, dim, string_id=None, qualifier=None):
        if dim != "" and dim < 0:
            Meta_Toolbox_Error("negative dimension for array")
        if string_id is None:
            string_id = new_c_name("array")
        self.c_var = c_variable(c_pointer(dtype), string_id)
        self.dtype = dtype
        self.dim = dim
        self.id = string_id
        self.vars = self.c_var.vars
        if qualifier != None:
            self.declaration_string = qualifier + " " + dtype
        else:
            self.declaration_string = dtype
        self.qualifier = qualifier

    def __repr__(self):
        # method for printing the c_variable inside Python code
        return self.c_var.__repr__()

    def declare(self, **kwargs):
        # returns C++ code to declare a fixed-size arry of size dim,
        # skipping declaration if dim=0
        if self.dim <= 0:
            return c_empty_instruction
        if self.qualifier == "extern __shared__":
            dim_string = ""
        else:
            dim_string = str(self.dim)
        local_vars = self.c_var.vars
        global_vars = set()
        return c_instruction(
            f"{self.declaration_string} {self.c_var}[{dim_string}]",
            local_vars,
            global_vars,
            **kwargs,
        )

    def split(self, *dims):
        # split c_array in n sub arrays with dimensions dims[0], dims[1], ..., dims[n-1]
        if sum(dims) != self.dim:
            Meta_Toolbox_Error("incompatible dimensions for split")
        listarr, cumdim = [], 0
        for dim in dims:
            listarr.append(c_array(self.dtype, dim, f"({self.id}+{cumdim})"))
            cumdim += dim
        return listarr

    def assign(self, val):
        # returns C++ code string to fill all elements of a fixed size array with a single value
        # val is a c_variable representing the value.
        loop, k = c_for_loop(0, self.dim, 1, pragma_unroll=True)
        return loop(self[k].assign(val))

    def __getitem__(self, other):
        other = py2c(other)
        if isinstance(other, c_expression):
            if other.dtype in ("int", "signed long int"):
                expression = f"{self.id}[{other.id}]"
            elif other.dtype == "float":
                expression = f"{self.id}[(int){other.id}]"
            elif other.dtype == "double":
                expression = f"{self.id}[(signed long int){other.id}]"
            else:
                Meta_Toolbox_Error(
                    "v[i] with i and v c_array requires i.dtype='int', i.dtype='signed long int', i.dtype='float' or i.dtype='double' "
                )
        else:
            Meta_Toolbox_Error("not implemented")
        vars = self.c_var.vars.union(other.vars)
        return c_lvalue(
            string_id=expression, vars=vars, dtype=self.dtype, add_parenthesis=False
        )

    @property
    def c_print(self):
        if self.dtype in ["float", "double"]:
            tag = "%f, " * self.dim
        elif self.dtype in ["int", "signed long int", "float*", "double*"]:
            tag = "%d, " * self.dim
        else:
            Meta_Toolbox_Error(f"c_print not implemented for dtype={self.dtype}")
        string = f'printf("{self.id} = {tag}\\n"'
        for i in range(self.dim):
            string += f", {self[i].id}"
        string += ");\n"
        return string
