#!/usr/bin/python
"""  """


def is_increment(arr):
    for i in range(1, len(arr)):
        if arr[i-1] >= arr[i]:
            return False
    return True

def is_decrement(arr):
    for i in range(1, len(arr)):
        if arr[i-1] <= arr[i]:
            return False
    return True

def get_inc_step(arr):
    i = -1
    while i >= -len(arr)+1:
        if arr[i-1] > arr[i]:
            break
        i -= 1
    return -i-1

def get_dec_step(arr):
    i = -1
    while i >= -len(arr)+1:
        if arr[i-1] < arr[i]:
            break
        i -= 1
    return -i-1

def get_over_step(vs, v):
    i = -1
    while i >= -len(vs)+1:
        if vs[i] > v:
            break
        i -= 1
    return -i-1

def get_below_step(vs, v):
    i = -1
    while i >= -len(vs)+1:
        if vs[i] < v:
            break
        i -= 1
    return -i-1

def is_more(arr, c=2):
    for i in range(c, len(arr)):
        if min(arr[i-c:i]) > arr[i]:
            return False
    return True

def is_less(arr, c=2):
    for i in range(c, len(arr)):
        if max(arr[i-c:i]) < arr[i]:
            return False
    return True

def get_more_step(arr, c=2):
    i = -1
    while i >= -len(arr)+c:
        if min(arr[i-c:i]) > arr[i]:
            break
        i -= 1

    if i == -1:
        return 0

    return -1-i

def get_less_step(arr, c=2):
    i = -1
    while i >= -len(arr)+c:
        if max(arr[i-c:i]) < arr[i]:
            break
        i -= 1

    if i == -1:
        return 0

    return -1-i

