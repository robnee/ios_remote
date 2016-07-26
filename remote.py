'''Home Theater Remote Control System

uses scene to implement a home theater touch interface. Delegates command sending to a controller class.

TODO:
    move title bar to each page (added to dispatch to root scene)
    create a macro class. or just add macros to subclass of controller
    DONE panels instead of scenes for pages
    DONE move assets info to a separate config class
    add docstrings
    change title bar when changing pages
    parameterize RemTVPage
    add a controller connection indicatior
    action on button down or button up?
'''

from scene import *
from myui import *
import ui
import json
import sound
import scene

import config
import controller


hostname = 'none'
'''Controller hostname control.

Hostname or ip address to connect to.  if set to None search for host.  Set to
'none' to suppress remote controller connection and just log sent commands.
'''


# -------------------------------------------------------------------------
# These functions are the actual remote control implementation
# -------------------------------------------------------------------------


class RemPowerOffScene(MyScene):
    '''Modal scene for power off confirmation'''
    def setup(self):
        self.background_color = (0.4, 0, 0, 0.3)
        self.z_position = 1
        
        size = Size(400, 300)
        self.panel = MyPanel(size, 'grey')
        self.panel.origin = self.panel.position = ((self.size.w - size.w) / 2, (self.size.h - size.h) / 2)
        self.add_child(self.panel)
        
        self.label = LabelNode('Power Off?')
        self.label.position = (size.w / 2, 20)
        self.panel.add_child(self.label)
        
        self.icon = SpriteNode('iow:power_256')
        self.icon.color = '#ddd'
        self.icon.position = (size / 2)
        self.panel.add_child(self.icon)
        
        MyScene.setup(self)
        
    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
    
        if self.panel.frame.contains_point(touch.location):
            pass
            #root.change_scene(root.blue_scene)
        else:
            root.dismiss_modal_scene()


class RemBatteryIndicator(SpriteNode):
    def __init__(self, parent):
        SpriteNode.__init__(self, texture='iow:battery_empty_256', )
        self.run_action(Action.repeat(
            Action.sequence(
                Action.wait(60),
                Action.call(RemBatteryIndicator.update, 1.0)
            ),
            0
        ))
        
        parent.add_child(self)
        
        self.update(0)
        
    def update(self, progress):
        # remember the size
        size = self.size
        level = RemBatteryIndicator.get_battery_level()
        if level < 0.12:
            self.texture = Texture('iow:battery_empty_256')
            self.color = cfg.titlebar.battery.alert_color
        elif level < 0.37:
            self.texture = Texture('iow:battery_low_256')
            self.color = 'white'
        elif level < 0.75:
            self.texture = Texture('iow:battery_half_256')
            self.color = 'white'
        else:
            self.texture = Texture('iow:battery_full_256')
            self.color = 'white'
        self.size = size
        
    def get_battery_level():
        '''battery level (0 - 1)'''
        import objc_util
        
        UIDevice = objc_util.ObjCClass('UIDevice')
        device = UIDevice.currentDevice()
        
        device.setBatteryMonitoringEnabled_(True)
        battery_level = device.batteryLevel()
        device.setBatteryMonitoringEnabled_(False)
        return battery_level

    
class RemConnectionIndicator(SpriteNode):
    def __init__(self, parent):
        SpriteNode.__init__(self, texture='iow:radio_waves_256')
        self.color = cfg.titlebar.connection.alert_color
        
        parent.add_child(self)
        
    def status_changed(self, status):
        if status == 'connected':
            self.color = 'white'
        elif status == 'sending':
            self.color = cfg.titlebar.connection.activity_color
        elif status == 'disconnected':
            self.color = cfg.titlebar.connection.alert_color
        

class RemTitlebar(ShapeNode, MyDispatch):
    '''Title bar with power off button'''
    def __init__(self, size, *args, **kwargs):
        path = ui.Path.rect(0, 0, size.w, cfg.titlebar.height)
        ShapeNode.__init__(self, path, fill_color=cfg.titlebar.color, *args, **kwargs)

        self.position = (size.w / 2, size.h - cfg.titlebar.height / 2)
        
        text = LabelNode(cfg.titlebar.title)
        self.add_child(text)
        self.z_position = 10
        
        side = cfg.titlebar.button_size
        power = MyImgButton(cfg.titlebar.power_button)
        power.position = (-size.w / 2 + cfg.titlebar.power_position, 0)
        power.action = lambda: root.change_scene(root.power_off_scene)
        power.repeat = False
        power.size = (side, side)  # make constants from these?
        
        self.add_child(power)
        
        n = MyImgButton(cfg.titlebar.back_button)
        n.position = (-size.w / 2 + cfg.titlebar.back_position, 0)
        n.action = lambda: root.change_page('POWERON')
        n.repeat = False
        n.size = (side, side)
        self.add_child(n)

        n = RemBatteryIndicator(parent=self)
        n.position = (-size.w / 2 + cfg.titlebar.battery_position, 0)
        n.size = (side, side)
        
        self.conn = RemConnectionIndicator(parent=self)
        self.conn.position = (-size.w / 2 + cfg.titlebar.connection_position, 0)
        self.conn.size = (side, side)

        self.layout()

        self.scene.controller.add_listener(self.conn.status_changed)
        
    def layout(self):
        '''adjust layout so children are visible'''
        for n in self.children:
            if n.position.x < -self.size.x / 2:
                n.position = Point(n.position.x + self.size.x, n.position.y)

               
class MyPage(MyDispatch, SpriteNode):
    '''Base class for pages for the remote'''
    def __init__(self, size):
        self.size = (size.w, size.h - cfg.titlebar.height)
        self.position = (0, 0)
        self.anchor_point = (0, 0)
        
        self.setup()
        

class RemPowerOnPage(MyPage):
    '''home screen for choosing activity'''
    def setup(self):
        self.color = cfg.poweron.background_color
        self.z_position = 1
        
        w, h = cfg.poweron.size
        size = Size(w, h)
        self.panel = p = MyPanel(size, cfg.poweron.panel_color)
        self.panel.origin = self.panel.position = ((self.size.w - size.w) / 2, (self.size.h - size.h) / 2)
        self.add_child(self.panel)

        margin = w / len(cfg.poweron.activities) / 2
        icon_size = cfg.poweron.icon_size
        icon_font = tuple(cfg.poweron.icon_font)

        label_offset = 20
        x = margin
        for label, icon, cmd, arg in cfg.poweron.activities:
            n = MyImgButton(icon)
            n.size = (icon_size, icon_size)
            n.position = (x, size.h / 2 + label_offset)
            n.action = lambda id=arg: root.change_page(id)
            p.add_child(n)
            
            l = LabelNode(label, icon_font)
            l.position = (x, size.h / 2 - icon_size / 2)
            l.action = lambda id=arg: root.change_page(id)
            p.add_child(l)
            
            x += margin * 2


class RemTVPage(MyPage):
    '''Page for broascast/cable TV activity'''
    def setup(self):
        self.panel = None
        
        self.color = cfg.tv.background_color
        self.z_position = 1

        self.menu = RemMenuPanel(Size(0, 0), cfg.tv.menu_color)
        self.add_child(self.menu)

        # create menu labels and add to menu
        font = tuple(cfg.tv.menu_font)
        for panel_id in cfg.tv.menu_order:
            title = cfg.tv.panels[panel_id]['title']
            c = MyLabelButton(title, font)
            c.color = cfg.tv.menu_label_color
            c.label_id = panel_id
            c.action = lambda panel_id=panel_id: self.change_panel(panel_id)
            self.menu.add_child(c)
        
        # volume panel
        self.vol = RemVolumePanel(Size(0, 0), cfg.tv.menu_color)
        self.add_child(self.vol)

        self.panels = dict()

        channel_size = cfg.tv.channel_size
        channel_font = tuple(cfg.tv.channel_font)
        for id in cfg.tv.panels:
            channel_color = cfg.tv.panels[id]['color']
            self.panels[id] = p = RemChannelPanel(Size(0, 0), cfg.tv.menu_color)
            p.alpha = 0
        
            for i in range(20):
                n = MyLabelButton('CHAN ' + str(i), channel_font, channel_color, Size(channel_size, channel_size))
                p.add_child(n)
                
        self.did_change_size()
        
        self.change_panel(cfg.tv.startup_panel)

    def did_change_size(self):
        landscape = self.size.w > self.size.h
        
        side = min(self.size)
        margin = side * cfg.tv.margin_pct / 100
        
        mside = cfg.tv.menu_height
        self.menu.position = (margin, self.size.h - margin - mside)
        self.menu.set_size(Size(side - 2 * margin, mside))
        self.menu.layout()
        
        # Volume panel
        vside = cfg.volume.size
        self.vol.position = (margin, margin)
        self.vol.set_size(Size(side * 0.4, vside))
        if landscape:
            self.vol.position = (side, margin)
        else:
            self.vol.position = (margin, margin)
        self.vol.layout()
          
        if landscape:
            cside = min(side, self.size.h - margin * 3 - mside)
        else:
            cside = min(side, self.size.h - margin * 4 - mside - vside)
        for id in self.panels:
            self.panels[id].position = (margin, self.size.h - cside - mside - 2 * margin)
            self.panels[id].set_size(Size(side - 2 * margin, cside))
            self.panels[id].layout()
        
    def change_panel(self, panel_id):
        panel = self.panels[panel_id]
        print('panel to', panel, panel_id, self.panel)
        if self.panel != panel:
            # fade out and remove current panel
            if self.panel is not None:
                self.panel.run_action(
                    Action.sequence(
                        Action.fade_to(0, 0.25),
                        Action.remove()
                    )
                )
            
            # load and fade in new panel
            self.panel = panel
            self.panel.alpha = 0
            self.add_child(panel)
            self.panel.run_action(Action.fade_to(1, 0.25))
            
            # update menu hilight
            for n in self.menu.children:
                if n.label_id == panel_id:
                    n.label.color = cfg.tv.menu_select_color
                else:
                    n.label.color = cfg.tv.menu_label_color


class RemMenuPanel(MyPanel):
    '''menu bar to select active channel panel'''
    def __init__(self, size, color):
        super().__init__(size, color)
        
    def layout(self):
        '''position node children in a grid'''

        # width of all menu items
        menu_width = 0
        for c in self.children:
            menu_width += c.size.w
    
        # compute margin between buttons
        ws = self.size.w - menu_width
        margin = ws / len(self.children)
        
        # perform layout
        x = margin / 2
        y = self.size.h / 2
        for c in self.children:
            c.origin = c.position = (x + c.size.w / 2, y)
            x += c.size.w + margin
    

class RemVolumePanel(MyPanel):
    '''volume and audio controls'''
    def __init__(self, size, color):
        super().__init__(size, color)
        
        w, h = self.size
        
        img0, cmd0, arg0 = cfg.volume.mute_off_button
        img1, cmd1, arg1 = cfg.volume.mute_on_button
        self.mute = MyToggle(img0, img1)
        self.add_child(self.mute)
        
        img, cmd, arg = cfg.volume.vol_up_button
        self.vol_up = MyImgButton(img)
        self.vol_up.action = lambda c=cmd, a=arg: root.controller.put(c, a)
        self.add_child(self.vol_up)

        img, cmd, arg = cfg.volume.vol_down_button
        self.vol_down = MyImgButton(img)
        self.vol_down.action = lambda c=cmd, a=arg: root.controller.put(c, a)
        self.add_child(self.vol_down)
        
    def layout(self):
        w, h = self.size
        button_size = cfg.volume.button_size

        self.mute.position = (w / 2, button_size)
        self.vol_up.position = (w - button_size, h - button_size)
        self.vol_down.position = (w - button_size, button_size)
        
         
class RemChannelPanel(MyPanel):
    '''groups channel buttons in a grid'''
    def __init__(self, size, color):
        super().__init__(size, color)
        
    def layout(self):
        '''position node children in a grid'''
        aspect_ratio = self.size.w / self.size.h
        
        # seek the proper snap grid
        for cols in range(1, 10):
            # trunate rows to test
            rows = int(cols / aspect_ratio)
            if len(self.children) <= rows * cols:
                break
            # round rows to test
            rows = round(cols / aspect_ratio)
            if len(self.children) <= rows * cols:
                break
        
        # Position children
        for i in range(len(self.children)):
            c = i % cols
            r = int(i / cols)
            x = self.size.w / cols * (c + 0.5)
            y = self.size.h / rows * (r + 0.5)
            
            self.children[i].position = (x, self.size.h - y)
        
        
class RemBluePage(MyPage):
    '''bluray page'''
    def setup(self):
        self.color = cfg.blue.background_color
        self.z_position = 1
        
        self.panel = MyPanel(Size(300, 200), 'grey')
        self.panel.origin = self.panel.position = (300, 400)
        self.add_child(self.panel)

    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        root.change_page('POWERON')


class RemWiiPage(MyPage):
    '''Wii game page'''
    def setup(self):
        self.color = cfg.wii.background_color
        self.z_position = 1
        
        self.panel = MyPanel(Size(300, 200), 'grey')
        self.panel.origin = self.panel.position = (300, 400)
        self.add_child(self.panel)

    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        root.change_page('POWERON')


class RemAppleTVPage(MyPage):
    '''Wii game page'''
    def setup(self):
        self.color = cfg.appletv.background_color
        self.z_position = 1
        
        self.panel = MyPanel(Size(300, 200), 'grey')
        self.panel.origin = self.panel.position = (300, 400)
        self.add_child(self.panel)

    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        root.change_page('POWERON')


class RemRootScene(MyScene):
    '''main Scene of remote app.  Receives and dispatches touch events'''
    def setup(self):
        self.disable_status()
        
        # set up controller communications
        self.controller = controller.MyController(hostname)

        self.titlebar = RemTitlebar(self.size, parent=self)
        
        self.power_off_scene = RemPowerOffScene()
        
        # set up page dict and instantiate page classes
        self.pages = dict()
        for page_id in cfg.pages:
            page_name = cfg.pages[page_id]
            class_name = cfg[page_name]['class_name']
            class_ = globals()[class_name]
            self.pages[page_id] = class_(self.size)
         
        self.controller.connect()
        
        # flip to startup page
        self.curr_page = None
        self.change_page(cfg.startup_page)

    def disable_status(self):
        from objc_util import ObjCInstance
        ObjCInstance(self.view).statusLabel().alpha = 0
                
    def change_page(self, page_id):
        new_page = self.pages[page_id]
        if self.curr_page is not None and self.curr_page != new_page:
            self.curr_page.run_action(
                Action.sequence(
                    Action.fade_to(0, 0.25),
                    Action.remove()
                )
            )
        
        # fade in new page
        new_page.alpha = 0
        self.curr_page = new_page
        self.add_child(new_page)
        self.curr_page.run_action(Action.fade_to(1, 0.25))
        
    def change_scene(self, s):
        if self.presented_scene:
            self.dismiss_modal_scene()
            #self.presented_scene.run_action(Action.fade_to(0, 0.5, TIMING_EASE_OUT))
        
        # Fade in new scene
        scene.alpha = 0
        self.present_modal_scene(s)
        scene.run_action(Action.fade_to(1, 0.25, TIMING_EASE_IN))

# --------------------------------------------------------------------------------


def get_config(filename):
    '''read json config file'''
        
    # load config from json file
    with open('config.json') as fp:
        return config.RemConfig(json.load(fp))


if __name__ == '__main__':
    cfg = get_config('config.json')
    
    global root
    root = RemRootScene()
    # orientation no longer really works
    run(root, orientation=LANDSCAPE)
