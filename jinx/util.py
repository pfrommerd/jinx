from contextlib import contextmanager
import time
import jax
from jax import custom_vjp
import jax.numpy as jnp

# returns a but disables backprop of gradients through the return value
@custom_vjp
def zero_grad(a):
    return a

def zero_grad_fwd(a):
    return a, None

def zero_grad_bkw(res, g):
    return None

zero_grad.defvjp(zero_grad_fwd, zero_grad_bkw)

# Scan with the first function call unrolled
# so that it can do special things (like initialize state)
def scan_unrolled(scan_fn, init, xs, length=None):
    if length is not None and length == 0:
        return init, None
    x_first = (
        jax.tree_map(lambda x: x[0] if x is not None else None, xs) 
        if xs is not None else None
    )
    x_remainder = (
        jax.tree_map(lambda x: x[1:] if x is not None else None, xs) 
        if xs is not None else None
    )
    carry, y = scan_fn(init, x_first)
    final_carry, ys = jax.lax.scan(scan_fn, carry, x_remainder,
        length=length - 1 if length is not None else None)
    # concatenate the first y onto the ys
    ys = tree_prepend(y, ys)
    return final_carry, ys

def tree_append(a, b):
    return jax.tree_util.tree_map(
        lambda a,b: jnp.concatenate((a, jnp.expand_dims(b,0))) if a is not None and b is not None else None,
        a,b
    )

def tree_prepend(a, b):
    return jax.tree_util.tree_map(
        lambda a,b: jnp.concatenate((jnp.expand_dims(a,0), b)) if a is not None and b is not None else None,
        a,b
    )

def ravel_dist(a,b, ord=None):
    x, _ = jax.flatten_util.ravel_pytree(a)
    y, _ = jax.flatten_util.ravel_pytree(b)
    return jnp.linalg.norm(x-y, ord=ord)