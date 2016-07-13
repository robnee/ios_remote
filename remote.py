'''Home Theater Remote Control System

uses scene to implement a home theater touch interface. Delegates command sending to a controller class.

TODO:
    move title bar to each page (added to dispatch to root scene)
    create a macro class. or just add macros to subclass of controller
    DONE panels instead of scenes for pages
    move assets info to a separate config class
    add docstrings
    change title bar when changing pages
    parameterize RemTVPage
    add a controller connection indicatior
'''

from scene import *
import ui
import sound
import scene

import config
import controller


hostname = 'none'
'''Controller hostname control.

Hostname or ip address to connect to.  if set to None search for host.  Set to
'none' to suppress remote controller connection and just log sent commands.
'''


class MyTarget:
    '''Touch target for UI. Gives feedback and optionally perform an action'''
    def __init__(self):
        self.action = None
        self.repeat = True
        
    def touch_began(self, touch):
        # flash the button to notify press
        self.run_action(
            Action.sequence(
                Action.fade_to(0.5, 0.05)
            )
        )

        # set the auto repeat timer
        if(self.repeat):
            self.run_action(
                Action.sequence(
                    Action.wait(0.75),
                    Action.repeat(
                        Action.sequence(
                            Action.call(lambda: self.touch_repeat(touch)),
                            Action.wait(0.25)
                        ),
                        25
                    )
                ),
                'repeat'
            )
        
        self.dispatch()
    
    def dispatch(self):
        print('pos:', self.position)
        sound.play_effect('8ve:8ve-tap-simple')
        if self.action is not None:
            self.action()
        
    def touch_repeat(self, touch):
        # hackish way to detect expiration of this touch by asking the root
        # if this is still a touch in flight. if not fade up. Attempting
        # to mess with the action from inside a callback is fatal though.
        if touch.touch_id in root.touches:
            print(touch, len(root.touches), root.touches)
            self.dispatch()
        else:
            self.fade_up()

    def cancel_repeat(self):
        self.remove_action('repeat')
          
    def fade_up(self):
        if self.alpha < 1.0:
            self.run_action(
                Action.sequence(
                    Action.fade_to(1.0, 0.05)
                )
            )
 
    def touch_ended(self, touch):
        # print('ended')
        self.fade_up()
        self.cancel_repeat()


class MyDispatch():
    '''Base class for collection of MyTarget classes. handles dispatch to targets'''
    def touch_began(self, touch):
        print('MyDispatch.touch_began', type(self).__name__, touch.location, len(self.children))
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyDispatch) or isinstance(x, MyTarget):
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_began(touch)
                    print(type(x).__name__)
                    return True
                    
        return False
                    
    def touch_ended(self, touch):
        # print('MyDispatch.touch_ended')
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyDispatch) or isinstance(x, MyTarget):
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_ended(touch)
                    return True
                    
        return False


class MyLabelButton(ShapeNode, MyTarget):
    '''Button by combining LabelNode with target handling'''
    def __init__(self, text, font, bgcolor=(0,0,0,0), size=None, shadow=None):
        MyTarget.__init__(self)
        
        self.label = LabelNode(text, font)
        self.add_child(self.label)

        sz = size if size else Size(self.label.size.w, self.label.size.w)
        path = ui.Path.rounded_rect(0, 0, sz.w, sz.h, sz.w / 10)
        path.line_width = 0
        ShapeNode.__init__(self, path=path, fill_color=bgcolor, shadow=shadow)
        

class MyImgButton(SpriteNode, MyTarget):
    '''Image Buttom via a SpriteNode with target handling'''
    def __init__(self, img):
        MyTarget.__init__(self)
        SpriteNode.__init__(self, img, color='green')
        self.size = (70, 70)
        self.color = 'white'


class MyToggle(MyImgButton):
    '''Toggle button class'''
    def __init__(self, img_f, img_t):
        MyImgButton.__init__(self, img_f)
        self.repeat = False
        self.img_f = img_f
        self.img_t = img_t
        self.state = False
                
    def toggle(self):
        if(self.state):
            self.state = False
            self.texture = Texture(self.img_f)
            self.size = (70, 70)
        else:
            self.state = True
            self.texture = Texture(self.img_t)
            self.size = (70, 70)
            
    def touch_ended(self, touch):
        self.toggle()
        MyImgButton.touch_ended(self, touch)


class MyScene(MyDispatch, Scene):
    '''Scene subclass that supports dispatch'''
    def setup(self):
        path = ui.Path.rect(0, 0, self.size.w, self.size.h)
        path.line_width = 0
        self.background = ShapeNode(path=path, fill_color=self.background_color)
        self.background.anchor_point = (0, 0)
        self.background.z_position = -1
        self.add_child(self.background)
        
    def touch_began(self, touch):
        if not MyDispatch.touch_began(self, touch):
            sound.play_effect('casino:CardSlide1')
            return False
            
        return True
            

class MyPanel(ShapeNode, MyDispatch):
    '''A panel for grouping targets.  supports dispatch'''
    def __init__(self, size, fill_color):
        path = ui.Path.rounded_rect(0, 0, size.w, size.h, 10)
        path.line_width = 0
        ShapeNode.__init__(self, path=path, fill_color=fill_color)
        
        self.size = size
        self.anchor_point = (0, 0)
        
             
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


class RemTitlebar(ShapeNode, MyDispatch):
    '''Title bar with power off button'''
    def __init__(self, size):
        path=ui.Path.rect(0, 0, size.w, config.titlebar.height)
        ShapeNode.__init__(self, path, fill_color=config.titlebar.color)

        self.position = (size.w / 2, size.h - config.titlebar.height / 2)
        
        text = LabelNode(config.titlebar.title)
        self.add_child(text)
        self.z_position = 10
        
        side = config.titlebar.button_size
        power = MyImgButton(config.titlebar.power_button)
        power.position = (-size.w / 2 + config.titlebar.height / 2, 0)
        power.action = lambda: root.change_scene(root.power_off_scene)
        power.repeat = False
        power.size = (side, side)  # make constants from these?
        
        self.add_child(power)
        
        n = MyImgButton(config.titlebar.back_button)
        n.position = (-250, 0)
        n.action = lambda: root.change_page('POWERON')
        n.repeat = False
        n.size = (side, side)
        self.add_child(n)

        
class MyPage(MyDispatch, SpriteNode):
    '''Base class for pages for the remote'''
    def __init__(self, size):
        self.size = (size.w, size.h - config.titlebar.height)
        self.position = (0, 0)
        self.anchor_point = (0, 0)
        
        self.setup()
        

class RemPowerOnPage(MyPage):
    '''home screen for choosing activity'''
    def setup(self):
        self.color = (0.2, 0.2, 0.2, 0.2)
        self.z_position = 1
        
        w, h = 600, 300
        size = Size(w, h)
        self.panel = p = MyPanel(size, 'grey')
        self.panel.origin = self.panel.position = ((self.size.w - size.w) / 2, (self.size.h - size.h) / 2)
        self.add_child(self.panel)
        
        assets = [
            ('TV', 'TV', 'iow:ios7_monitor_outline_256'),
            ('APPLETV', 'TV', 'iow:social_apple_outline_256'),
            ('WII', 'Wii', 'iow:game_controller_b_256'),
            ('BLUE', 'Bluray', 'iow:disc_256')
        ]
        margin = w / 8
        x = margin
        for page_id, label, icon in assets:
            n = MyImgButton(icon)
            n.size = (120, 120)
            n.position = (x, size.h / 2 + 20)
            n.action = lambda id=page_id: root.change_page(id)
            p.add_child(n)
            
            l = LabelNode(label, ('Helvetica', 30))
            l.position = (x, size.h / 2 - 120 / 2)
            l.action = lambda id=page_id: root.change_page(id)
            p.add_child(l)
            
            x+= margin * 2


class RemTVPage(MyPage):
    '''Page for broascast/cable TV activity'''
    def setup(self):
        self.panel = None
        
        self.color = config.tv.background_color
        self.z_position = 1
        
        side = min(self.size)
        margin = side * config.tv.margin_pct / 100
        
        mside = config.tv.menu_height
        menu_color = config.tv.menu_color
        self.menu = RemMenuPanel(Size(side - 2 * margin, mside), menu_color)
        self.menu.position = (margin, self.size.h - margin - mside)
        
        self.assets = [
            ('BCAST', 'Broadcast', 'darkblue', 90),
            ('NEWS', 'News', 'darkred', 90),
            ('ENTER', 'Entertainment', 'purple', 90),
            ('SPORTS', 'Sports', 'green', 90),
            ('MOVIES', 'Movies', 'goldenrod', 90)
        ]

        # create menu labels and add to menu
        font = tuple(config.tv.menu_font)
        for a in self.assets:
            id, title, color, sz = a                       
            c = MyLabelButton(title, font)
            c.color = config.tv.menu_font_color
            c.label_id = id
            c.action = lambda panel_id=id: self.change_panel(panel_id)
            self.menu.add_child(c)
            
        self.menu.layout()
        self.add_child(self.menu)
    
        # volume panel
        vside = 200
        self.vol = RemVolumePanel(Size(side * 0.4, vside), menu_color)
        self.vol.origin = self.vol.position = (margin, margin)
        self.add_child(self.vol)
        
        cside = min(side, self.size.h - margin * 4 - mside - vside)

        self.panels = dict()

        for a in self.assets:
            id, title, button_color, sz  = a
            self.panels[id] = p = RemChannelPanel(Size(side - 2 * margin, cside), menu_color)
            p.position = (margin, self.size.h - cside - mside - 2 * margin)
            p.alpha = 0
        
            for i in range(20):
                n = MyLabelButton('CHAN ' + str(i), ('Arial Rounded MT Bold', 20), button_color, Size(sz, sz))
                p.add_child(n)
            p.layout()
        
        self.change_panel(config.tv.startup_panel)

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
                    n.label.color = config.tv.menu_select_color
                else:
                    n.label.color = config.tv.menu_font_color


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

        n = MyToggle('iow:volume_low_256', 'iow:volume_mute_256')
        n.position = (w / 2, 50)
        self.add_child(n)

        n = MyImgButton('iow:chevron_up_256')
        n.position = (w - 50, h - 50)
        n.action = lambda: root.controller.put('@MAIN:VOL', 'Up')
        self.add_child(n)

        n = MyImgButton('iow:chevron_down_256')
        n.position = (w - 50, 50)
        n.action = lambda: root.controller.put('@MAIN:VOL', 'Down')
        self.add_child(n)
        
         
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
            rows = int(cols / aspect_ratio + 0.5)
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
        self.color = (0, 0, 0.5, 0.5)
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
        self.color = (0, 0.4, 0)
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
        self.color = (0.4, 0.4, 0)
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

        title = RemTitlebar(self.size)
        self.add_child(title)
        
        self.power_off_scene = RemPowerOffScene()
        
        # set up page dict and instantiate page classes
        self.pages = dict()
        for page_id in config.pages:
            page_name = config.pages[page_id]
            class_name = config[page_name]['class_name']
            class_ = globals()[class_name]
            self.pages[page_id] = class_(self.size)
         
        # flip to startup page   
        self.curr_page = None
        self.change_page(config.startup_page)
        
    def touch_began(self, touch):
        handled = super().touch_began(touch)
        print('handled', handled)
        
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
        
    def change_scene(self, scene):
        if self.presented_scene:
            self.dismiss_modal_scene()
            #self.presented_scene.run_action(Action.fade_to(0, 0.5, TIMING_EASE_OUT))
        
        # Fade in new scene
        scene.alpha = 0
        self.present_modal_scene(scene)
        scene.run_action(Action.fade_to(1, 0.25, TIMING_EASE_IN))

# --------------------------------------------------------------------------------

def get_class(class_name):
            page_info = self.pages[page_id]
            class_name = page_info['class_name']
            page_info['page'] = globals()[class_name](self.size)

if __name__ == '__main__':
    config = config.get_config()
    
    root = RemRootScene()
    # orientation no longer really works
    run(root, orientation=LANDSCAPE)
