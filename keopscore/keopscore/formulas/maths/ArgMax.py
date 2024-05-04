from keopscore.formulas.Operation import Operation
from keopscore.formulas.variables.Zero import Zero
from keopscore.utils.meta_toolbox import (
    c_zero_float,
    c_for_loop,
    c_if,
    c_variable,
    c_instruction_from_string,
)
from keopscore.utils.misc_utils import KeOps_Error

############################
######    ArgMax       #####
############################


class ArgMax(Operation):
    string_id = "ArgMax"

    def __init__(self, f):
        super().__init__(f)
        if f.dim < 1:
            KeOps_Error("ArgMax operation is only possible when dimension is non zero.")
        self.dim = 1

    def Op(self, out, table, arg):
        tmp = c_variable(out.dtype)
        loop, k = c_for_loop(1, arg.dim, 1, pragma_unroll=True)
        res = out.value.assign(c_zero_float) + tmp.declare_assign(arg[0])
        if out.dtype == "half2":
            loop_string = f"""
                // we have to work element-wise...
                __half2 cond = __hlt2({tmp},{arg[k]});                          // cond = (tmp > outF[k]) (element-wise)
                __half2 negcond = __float2half2_rn(1.0f)-cond;                        // negcond = 1-cond
                {out[0]} = cond * __float2half2_rn({k}) + negcond * {out[0]};    // out  = cond * k + (1-cond) * out 
                {tmp} = cond * {arg[k]} + negcond * {tmp};                   // tmp  = cond * outF[k] + (1-cond) * tmp
                            """
            body = c_instruction_from_string(loop_string)
            res += loop(body)
        else:
            res += loop(c_if(arg[k] > tmp, tmp.assign(arg[k]) + out.assign(k)))

        return res

    def DiffT_fun(self, v, gradin):
        return Zero(v.dim)

    # parameters for testing the operation (optional)
    enable_test = True  # enable testing for this operation
    nargs = 1  # number of arguments
    test_argdims = [5]  # dimensions of arguments for testing
    torch_op = "lambda x : torch.argmax(x, dim=-1, keepdim=True).type(x.dtype)"
    no_torch_grad = True
