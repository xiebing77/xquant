#!/usr/bin/python3
import sys
import json

def createInstance(module_name, class_name, *args, **kwargs):
    module_meta = __import__(module_name, globals(), locals(), [class_name])
    class_meta = getattr(module_meta, class_name)
    obj = class_meta(*args, **kwargs)
    return obj

if __name__ == "__main__":

    module_name = sys.argv[1].replace('/', '.')
    class_name = sys.argv[2]
    config = json.loads(sys.argv[3])
    if len(sys.argv)>=5:
        debug = bool(sys.argv[4])
    else:
        debug = False

    obj = createInstance(module_name, class_name, config, debug)
    obj.run()
