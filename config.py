'''Rob's Remote Control Config

this is a json representation of the configuration (size, layout, colors, codes etc) for the scen-based remote control.
'''

import json

robs_remote = '''
{
    "titlebar": {
        "title": "Rob's Remote",
        "height": 50,
        "color": "grey"
    },
    "pages": {
        "POWERON": {
            "class": "RemPowerOnPage"
        },
        "BLUE": {
            "class": "RemBluePage"
        },
        "TV": {
            "class": "RemTVPage"
        },
        "WII": {
            "class": "RemWiiPage"
        },
        "APPLETV": {
            "class": "RemAppleTVPage"
        }
    },

    "startup_page": "POWERON"
}
'''


class MyConfig():
    '''class to store the config heirarchy in json.  coverts from dict to class'''
    def __init__(self, d):
        '''convert a dict into class attributes for easy reference'''
        for key in d.keys():
            if type(d[key]) is dict:
                c = MyConfig(d[key])
                setattr(self, key, c)
                setattr(self, '_' + key, d[key])
            else:
                setattr(self, key, d[key])


def get_config():
    return MyConfig(json.loads(robs_remote))

    
if __name__ == '__main__':
    config = get_config()
    print(config.titlebar.height)
