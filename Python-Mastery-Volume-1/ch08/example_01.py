import dis

def demonstration_function(x: int) -> int:
    try:
        val = 100 // x
    except ZeroDivisionError:
        val = 0
    return val

dis.dis(demonstration_function)
