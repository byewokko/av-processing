import math


def log_quad(x, zero, base=10, *args):
    return math.log((x-zero)**2 + 1, base)


def cos(x, zero, f=1, *args):
    return 1 - math.cos(2*math.pi*f*(x-zero))


def norm(x, zero, sigma=1, *args):
    return 1 - math.exp(-0.5*((x-zero)/sigma)**2)


def saw(x, zero, mod=1/3, *args):
    return (x-zero) % mod


funcs = {"abs": lambda x, zero, *args: abs(x-zero), 
         "neg-abs": lambda x, zero, *args: 1 - abs(x-zero), 
         "quad": lambda x, zero, *args: (x-zero)**2, 
         "neg-quad": lambda x, zero, *args: 1 - (x-zero)**2, 
         "log-quad": log_quad, 
         "cos": cos,
         "norm": norm,
         "saw": saw}
