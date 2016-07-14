'''Rob's Remote Control Config

this is a json representation of the configuration (size, layout, colors, codes etc) for the scen-based remote control.
'''

import json


class RemConfig():
    '''class to store the config heirarchy in json.  coverts from dict to class'''
    def __init__(self, d):
        '''convert a dict into class attributes for easy reference'''
        for key in d.keys():
            value = d[key]
            if type(value) is dict:
                setattr(self, key, RemConfig(value))
            elif 'color' in key and type(value) is list:
                setattr(self, key, tuple(value))
            else:
                setattr(self, key, value)
        self.class_dict = d
                
    def __iter__(self):
        return iter(self.class_dict)
               
    def __getitem__(self, item):
        return self.class_dict[item]
        

if __name__ == '__main__':
    # load config from json file
    with open('config.json') as fp:
        config = RemConfig(json.load(fp))
    
    print(config.titlebar.height)
    
    print(dir(config))
    print(dir(config.pages))
    print(config.titlebar['height'])
    
    print(config.tv.menu_color)
    print(config.tv.background_color)
