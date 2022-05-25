

def base_to_list(n, base=10):
    result = []
    n = int(n)
    while(n):
        result.append(n%base)
        n //= base
    result.reverse()
    return result

def list_to_str(l):
    l = ""
    for each in l:
        l += str(l)
    return l
    