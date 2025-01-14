import paddle.fluid as fluid
import paddle
from . import cuda
from . import  nn
import os
import paddorch.nn.functional
import paddorch.nn.init
from paddle.fluid import dygraph
import numpy as np
from paddorch.tensor import varbase_to_tensor,Tensor
from . import optim
from . import  vision

double="float32"

def chunk(self , chunks , dim ):
    slices= fluid.layers.unstack(self, axis=dim, num=None)
    out_list=[]
    step=int(np.ceil(len(slices)/chunks))
    for st in range(0,len(slices),step):
        out_list.append(varbase_to_tensor(fluid.layers.concat( [paddle.fluid.layers.unsqueeze(x, dim, name=None) for x in slices[st:(st+step)] ], axis=dim, name=None)))
    return out_list

def trace(x, offset=0, dim1=0, dim2=1, out=None):
    return Tensor(fluid.layers.trace(x,offset,dim1,dim2,out))


def bmm(x,y):
    return Tensor(fluid.layers.bmm(x,y))
def eye(n , m ):
    return Tensor(fluid.layers.eye(n,m))

def dot(x,y):
    return Tensor(fluid.layers.dot(x,y))
def mm(x,y):
    return matmul(x,y)

def narrow(x, dim, start, length):
    return  fluid.layers.slice(x,[dim],[start],[start+length] )

def squeeze(x,axes=[-1]):
    return Tensor(fluid.layers.squeeze(x,axes))

def split(x,batch_size,dim=0):

    if not isinstance(batch_size,int):
        Y=[]
        st=0
        for bs in batch_size: #list of split size
            ed=st+bs
            Y.append(x[st:ed])
            st=ed

    else:
        n_splits = x.shape[0] // batch_size
        last_index=n_splits*batch_size
        Y= fluid.layers.split(x[:last_index],n_splits,dim=dim)
    # if last_index != x.shape[0]: ##handle not equal divide case
    #     Y.append(x[last_index:])
    return Y

def empty(*size):
    return zeros(*size)

def matmul(x,y):
    return Tensor(fluid.layers.matmul(x,y ))
def tensor(x,dtype=np.float32):
    if isinstance(x,list):
        x=np.array(x,dtype=dtype)
    if isinstance(x,int) or isinstance(x,np.int64):
        return zeros(x)
    return Tensor(x)

def FloatTensor(x):
    if isinstance(x,int):
        return zeros(x)
    return tensor(x)

def abs(x):
    return fluid.layers.abs(x)
def max(x,dim=None,keepdim=False):
    return varbase_to_tensor(fluid.layers.reduce_max(x,dim,keep_dim= keepdim ))

def min(x,dim=None,keepdim=False):
    return varbase_to_tensor(fluid.layers.reduce_min(x,dim,keep_dim= keepdim ))

def full_like(x,fill_value):
    return Tensor.new_full(x,x.shape,fill_value)

def norm(input, p="fro", dim=None, keepdim=False, out=None, dtype=None):
    from . import linalg
    return Tensor(linalg.norm(input, p=p, axis=dim, keepdim=keepdim,   name=None))


def where(condition, x=None, y=None):
    if  x is None:
        return fluid.layers.where(condition)
    else:
        w=condition.astype("float32")
        z=w*x+(1-w)*y
        return z
        # for i, flag in  enumerate(condition.numpy()) :
        #     if flag:
        #         out.append(x[i])
        #     else:
        #         out.append(y[i])
        # return stack(out)

def flip(self, dim):
    return Tensor(fluid.layers.flip(self,dims=[dim]))

def take(x,indices):
    if len(indices[0])==2:
        return stack([x[a[0],a[1]] for a in indices])
    if len(indices[0]) == 1:
        return stack([x[a[0]] for a in indices])

def linspace(start, stop, num, dtype="float32"):
    return Tensor(fluid.layers.linspace(start, stop, num, dtype))

def randint(low, high, size ,
           dtype="int64", requires_grad=False):
    return Tensor(fluid.layers.randint(low,
            high=high,
            shape=size,
            out=None,
            dtype=dtype,
            device=None,
            stop_gradient=not requires_grad))

def copy(src,target):
    # target.set_value(src)
    # return target
    fluid.layers.assign(src,target)

def rsqrt(x):
    return varbase_to_tensor(paddle.fluid.layers.rsqrt(x, name=None))

def sum(x,dim=None, keepdim=False):
    return varbase_to_tensor(fluid.layers.reduce_sum(x,dim,keepdim))

def sqrt(x):
    return varbase_to_tensor(fluid.layers.sqrt(x))
def pow(x,y):
    return varbase_to_tensor(fluid.layers.pow(x,y))

def as_tensor(x,dtype=np.float32):
    return tensor(x,dtype)

def is_tensor(x):
    return isinstance(x, ( dygraph.core.VarBase,  dygraph.framework.Variable,
                        dygraph.framework.ComplexVariable))

def manual_seed(seed):
    fluid.Program.random_seed=seed
    np.random.seed(seed)

def multinomial(weights , num_samples , replacement=False):
    select_samples=[]
    if not replacement and num_samples>len(weights):
        raise(Exception("num_samples should be no greater than the weights length"))

    while len(select_samples)<num_samples:
        x=fluid.layers.sampling_id(fluid.layers.reshape(weights,[1,-1] ))
        if not replacement:
            if x in select_samples:
                continue
        select_samples.append(x)
    return  select_samples
def LongTensor(x):
    if isinstance(x,int):
        return Tensor(fluid.Tensor)
    if isinstance(x,list):
        x=np.array(x,dtype=np.int32)
    return Tensor(x )

def stack(inputs,dim=0,out=None):
    x= fluid.layers.stack(inputs ,axis=dim )
    if out is None:
        return varbase_to_tensor(x)
    else:
        fluid.layers.assign(x,out)
        return out
def arange(*args,**kwargs):
    return Tensor(np.arange(*args,**kwargs).astype("int32"))
    # if end==0:
    #     return []
    # return varbase_to_tensor(paddle.fluid.layers.range(0, end, step, dtype))

def device(name):
    if name.startswith("cuda"):
        device_id=name.replace("cuda","").replace(":","")
        if len(device_id)==0:
            return fluid.CUDAPlace(0)
        else:
            return fluid.CUDAPlace(int(device_id))
    else:
        return fluid.CPUPlace()

def cat(tensors, dim=0, out=None):
    x=fluid.layers.concat(tensors,axis=dim)
    if out is None:
        return varbase_to_tensor(x)
    else:
        fluid.layers.assign(x,out)
        return out


def ones(*size, out=None, dtype="float32",device=None):
    return varbase_to_tensor(fluid.layers.ones(size,dtype))

def zeros(*size, out=None, dtype="float32",device=None,requires_grad=True):
    X= varbase_to_tensor(fluid.layers.zeros(size,dtype))
    if not requires_grad:
        X.stop_gradient=True
    return X

def ones_like(x, out=None,device=None):
    return varbase_to_tensor(fluid.layers.ones_like(x,out))

def cov(m, rowvar=False, inplace=False):
    '''Estimate a covariance matrix given data.

    Covariance indicates the level to which two variables vary together.
    If we examine N-dimensional samples, `X = [x_1, x_2, ... x_N]^T`,
    then the covariance matrix element `C_{ij}` is the covariance of
    `x_i` and `x_j`. The element `C_{ii}` is the variance of `x_i`.

    Args:
        m: A 1-D or 2-D array containing multiple variables and observations.
            Each row of `m` represents a variable, and each column a single
            observation of all those variables.
        rowvar: If `rowvar` is True, then each row represents a
            variable, with observations in the columns. Otherwise, the
            relationship is transposed: each column represents a variable,
            while the rows contain observations.

    Returns:
        The covariance matrix of the variables.
    '''
    if m.dim() > 2:
        raise ValueError('m has more than 2 dimensions')
    if m.dim() < 2:
        m = m.view(1, -1)
    if not rowvar and m.size(0) != 1:
        m = m.permute(1, 0)
    # m = m.type(torch.double)  # uncomment this line if desired
    fact = 1.0 / (m.size(1) - 1)
    if inplace:
        m -= mean(m, dim=1, keepdim=True)
    else:
        m = m -  mean(m, dim=1, keepdim=True)
    m = paddorch.Tensor(m)

    mt = m.permute(1, 0)  # if complex: mt = m.t().conj()
    return fact * fluid.layers.matmul(m, mt)


def zeros_like(x, out=None,device=None):
    return varbase_to_tensor(fluid.layers.zeros_like(x,out))

def randn(*shape, requires_grad=True):
    X= varbase_to_tensor(fluid.layers.randn(shape))
    if not requires_grad:
        X.stop_gradient=True
    return X

def mean(input):
    return  fluid.layers.mean(input)

def var(input, dim=None, keepdim=False, unbiased=True, name=None):
    if isinstance(dim,tuple):
        dim=list(dim)
    rank = len(input.shape)
    dims = dim if dim != None and dim != [] else range(rank)
    dims = [e if e >= 0 else e + rank for e in dims]
    inp_shape = input.shape
    mean = fluid.layers.reduce_mean(input, dim=dim, keep_dim=True, name=name)
    tmp = fluid.layers.reduce_mean((input - mean)**2, dim=dim, keep_dim=keepdim, name=name)
    if unbiased:
        n = 1
        for i in dims:
            n *= inp_shape[i]
        factor = n / (n - 1.0) if n > 1.0 else 0.0
        tmp *= factor
    return tmp
def mean(input, dim=None, keepdim=False, out=None):
    if isinstance(dim,tuple):
        dim=list(dim)
    x= fluid.layers.reduce_mean(input,dim,keepdim)
    if out is None:
        return varbase_to_tensor(x)
    else:
        fluid.layers.assign(x,out)
        return out

def lerp(input, end, weight, out=None):
    x= input+float(weight)*(end-input)
    if out is None:
        return x
    else:
        fluid.layers.assign(x,out)
        return out

def flatten(x,dim=1):
    x=fluid.layers.flatten(x ,axis=dim)
    return varbase_to_tensor(x)

def clamp(input, min, max, out=None) :
    return varbase_to_tensor(fluid.layers.clip(input, min, max))

def  no_grad(func=None):
    return fluid.dygraph.no_grad(func)

def check_if_state_dict(obj):
    '''
        check if the obj is a state_dict from paddle model
    '''
    first_key=list(obj.keys())[0]
    try:
        obj[first_key].name
        return True
    except:
        return False
def save(dict_obj, filename):
    '''
    save dict of state dict as a folder , or state dict as a file
    '''
    try:
        if check_if_state_dict(dict_obj):
            if filename.endswith(".pdparams"):
                filename=filename.replace(".pdparams","")
            fluid.dygraph.save_dygraph(dict_obj,filename)
        else:
            os.makedirs(filename,exist_ok=True)
            for key in dict_obj:

                    fluid.dygraph.save_dygraph( dict_obj[key], filename+"/"+str(key) )
    except Exception as E:
        print(E)


def load(file_path,map_location=None) :
    import glob
    out_dict=dict()
    if os.path.isdir(file_path):
        for fn in glob.glob(file_path+"/*.pdparams"):
            print(fn)
            key=os.path.basename(fn).replace(".pdparams","")
            out_dict[key]=fluid.dygraph.load_dygraph(fn)[0]

    else:
        out_dict=fluid.dygraph.load_dygraph(file_path)[0]

    return out_dict

def sigmoid(x):
    return Tensor(fluid.layers.sigmoid(x))
def tanh(x):
    return Tensor(fluid.layers.tanh(x))

def transpose(x,*perm):
    return x.transpose(*perm)