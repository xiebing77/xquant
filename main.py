#!/usr/bin/python3
import sys
import json

def createInstance(module_name, class_name, *args, **kwargs):
    #print("args  :", args)
    #print("kwargs:", kwargs)
    module_meta = __import__(module_name, globals(), locals(), [class_name])
    class_meta = getattr(module_meta, class_name)
    obj = class_meta(*args, **kwargs)
    return obj

if __name__ == "__main__":

    #print(sys.argv)
    module_name = sys.argv[1].replace('/', '.')
    class_name = sys.argv[2]
    strategy_config = json.loads(sys.argv[3])
    engine_config = json.loads(sys.argv[4])
    if len(sys.argv)>=6:
        debug = bool(sys.argv[5])
    else:
        debug = False
    
    obj = createInstance(module_name, class_name, strategy_config, engine_config, debug)
    obj.run()
