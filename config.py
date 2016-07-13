'''Rob's Remote Control Config

this is a json representation of the configuration (size, layout, colors, codes etc) for the scen-based remote control.
'''

import json

robs_remote = '''
{
    "startup_page": "POWERON",
        
    "titlebar": {
        "title": "Rob's Remote",
        "height": 50,
        "color": "grey",
        "button_size": 40,
        "power_button": "iow:power_256",
        "back_button": "iow:ios7_undo_256"
    },
    
    "pages": {
        "POWERON": "poweron",
        "BLUE": "blue",
        "TV": "tv",
        "WII": "wii",
        "APPLETV": "appletv"
    },

    "poweron": {
        "class_name": "RemPowerOnPage"
    },
    
    "blue": {
        "class_name": "RemBluePage"
    },
    "tv": {
        "class_name": "RemTVPage",
        "menu_height": 50,
        "menu_color": "grey",
        "menu_font": ["Arial Rounded MT Bold", 20],
        "menu_font_color": "white",
        "menu_select_color": "lightgrey",
        "margin_pct": 5,
        "background_color": [0.1, 0.1, 0.1],
        "startup_panel": "NEWS"
    },
    "wii": {
        "class_name": "RemWiiPage"
    },
    "appletv": {
        "class_name": "RemAppleTVPage"
    }
}
'''


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
        

def get_config():
    return RemConfig(json.loads(robs_remote))

    
if __name__ == '__main__':
    config = get_config()
    print(config.titlebar.height)
    
    print(dir(config))
    print(dir(config.pages))
    print(config.titlebar['height'])
    
    print(config.tv.menu_color)
    print(config.tv.background_color)
