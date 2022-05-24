

def base_to_list(n, base=10):
    result = []
    while(n):
        result.append(n%base)
        n //= base
    result.reverse()
    return result