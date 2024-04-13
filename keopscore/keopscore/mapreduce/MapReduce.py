from keopscore.formulas.reductions import *
from keopscore.formulas.GetReduction import GetReduction
from keopscore.utils.code_gen_utils import Var_loader, new_c_varname, pointer, c_include


class MapReduce:
    """
    base class for map-reduce schemes
    """

    def __init__(
        self,
        red_formula_string,
        aliases,
        nargs,
        dtype,
        dtypeacc,
        sum_scheme_string,
        tagHostDevice,
        tagCpuGpu,
        tag1D2D,
        use_half,
        use_fast_math,
        device_id,
    ):
        self.red_formula_string = red_formula_string
        self.aliases = aliases

        self.red_formula = GetReduction(red_formula_string, aliases=aliases)

        self.dtype = dtype
        self.dtypeacc = dtypeacc
        self.nargs = nargs
        self.sum_scheme_string = sum_scheme_string
        self.tagHostDevice, self.tagCpuGpu, self.tag1D2D = (
            tagHostDevice,
            tagCpuGpu,
            tag1D2D,
        )
        self.use_half = use_half
        self.use_fast_math = use_fast_math
        self.device_id = device_id
        self.varloader = Var_loader(
            self.red_formula, force_all_local=self.force_all_local
        )

    def get_code(self):
        self.headers = "#define C_CONTIGUOUS 1\n"

        if self.use_half == 1:
            self.headers += "#define USE_HALF 1\n"
            self.headers += c_include("cuda_fp16.h")
        else:
            self.headers += "#define USE_HALF 0\n"

        red_formula = self.red_formula
        formula = red_formula.formula
        dtype = self.dtype
        dtypeacc = self.dtypeacc
        nargs = self.nargs

        self.i = i = c_variable("signed long int", "i")
        self.j = j = c_variable("signed long int", "j")

        self.sum_scheme = eval(self.sum_scheme_string)(red_formula, dtype, dtypeacc, i)

        self.fout = self.sum_scheme.fout
        self.acc = self.sum_scheme.acc
        self.outi = self.sum_scheme.outi

        nx = c_variable("signed long int", "nx")
        ny = c_variable("signed long int", "ny")

        self.xi = c_array(dtype, self.varloader.dimx_local, "xi")
        self.param_loc = c_array(dtype, self.varloader.dimp_local, "param_loc")

        argname = new_c_varname("arg")
        self.arg = c_variable(pointer(pointer(dtype)), argname)
        self.args = [self.arg[k] for k in range(nargs)]
