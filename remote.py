'''Home Theater Remote Control System

uses scene to implement a home theater touch interface. Delegates command sending to a controller class.

TODO:
    move title bar to each page (added to dispatch to root scene)
    create a macro class. or just add macros to subclass of controller
    DONE panels instead of scenes for pages
    move assets info to a separate config class
    add docstrings
    change title bar when changing pages
'''

from scene import *
import ui
import sound
import scene
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
    def __init__(self, text, font, bgcolor=(0,0,0,0), size=None):
        MyTarget.__init__(self)
        
        l = LabelNode(text, font)
        self.add_child(l)

        sz = size if size else Size(l.size.w, l.size.w)
        path = ui.Path.rounded_rect(0, 0, sz.w, sz.h, sz.w/10)
        path.line_width = 0
        ShapeNode.__init__(self, path=path, fill_color=bgcolor)
        

class MyImgButton(SpriteNode, MyTarget):
    '''Image Buttom via a SpriteNode with target handling'''
    def __init__(self, img):
        MyTarget.__init__(self)
        SpriteNode.__init__(self, img, color='green')
        self.size = (70, 70)
        self.color = 'white'


class MyToggle(MyImgButton):
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
    def __init__(self, size, fill_color):
        path = ui.Path.rounded_rect(0, 0, size.w, size.h, 10)
        path.line_width = 0
        ShapeNode.__init__(self, path=path, fill_color=fill_color)
        
        self.size = size
        self.anchor_point = (0, 0)
        
             
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

TITLE_H = 50


class RemTitlebar(ShapeNode, MyDispatch):
    def __init__(self, title, size, background_color):
        ShapeNode.__init__(self, path=ui.Path.rect(0, 0, size.w, TITLE_H),
                           fill_color=background_color)
        text = LabelNode(title)
        self.add_child(text)
        self.z_position = 10

        power = MyImgButton('iow:power_256')
        power.position = (-size.w / 2 + 25, 0)
        power.action = lambda: root.change_scene(root.power_off_scene)
        power.repeat = False
        power.size = (40, 40)  # make constants from these?
        self.add_child(power)
        
        
class MyPage(MyDispatch, SpriteNode):
    def __init__(self, size):
        self.size = (size.w, size.h - TITLE_H)
        self.position = (0, 0)
        self.anchor_point = (0, 0)
        
        self.setup()
        

class RemPowerOffScene(MyScene):
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


class RemPowerOnPage(MyPage):
    def setup(self):
        self.color = (0.2, 0.2, 0.2, 0.2)
        self.z_position = 1
        
        size = Size(600, 300)
        self.panel = p = MyPanel(size, 'grey')
        self.panel.origin = self.panel.position = ((self.size.w - size.w) / 2, (self.size.h - size.h) / 2)
        self.add_child(self.panel)
        
        assets = [
            ('TV', 'TV', 'iow:ios7_monitor_outline_256'),
            ('APPLETV', 'TV', 'iow:social_apple_outline_256'),
            ('WII', 'Wii', 'iow:game_controller_b_256'),
            ('BLUE', 'Bluray', 'iow:disc_256')
        ]
        x = 0
        for page_id, label, icon in assets:
            x += 125
            n = MyImgButton(icon)
            n.size = (120, 120)
            n.position = (x, size.h / 2 + 20)
            n.action = lambda id=page_id: root.change_page(id)
            p.add_child(n)
            
            l = LabelNode(label, ('Helvetica', 30))
            l.position = (x, size.h/2 - 120/2)
            l.action = lambda: root.change_page(page_id)
            p.add_child(l)


class RemTVPage(MyPage):
    def setup(self):
        self.color = (0.1, 0.1, 0.1)
        self.z_position = 1

        side = min(self.size)
        
        margin = side / 20
        menu = MyPanel(Size(side * 0.9, TITLE_H), 'grey')
        menu.position = (margin, self.size.h - margin - TITLE_H)
        self.add_child(menu)
    
        # volume panel
        vside = 200
        self.panel = RemVolumePanel(Size(side * 0.4, vside), 'grey')
        self.panel.origin = self.panel.position = (side/20, side/20)
        self.add_child(self.panel)
        
        cside = min(side, self.size.h - margin * 4 - TITLE_H - vside)
        
        p = RemChannelPanel(Size(side * 0.9, cside), 'grey')
        p.position = (margin, self.size.h - cside - TITLE_H - 2 * margin)
        for i in range(20):
            n = MyLabelButton('HBO ' + str(i), ('Helvetica', 20), 'gold', Size(90, 90))
            p.add_child(n)
        p.layout()
        self.add_child(p)


class RemVolumePanel(MyPanel):
    '''volume and audio controls'''
    def __init__(self, size, color):
        super().__init__(size, color)

        n = MyLabelButton('▶️', ('Helvetica', 80))
        n.position = (50, 50)
        n.action = lambda: root.change_page('BLUE')
        self.add_child(n)
        
        w, h = self.size
        n = MyLabelButton('🔵', ('Helvetica', 80))
        n.position = (50, h - 50)
        n.action = lambda: root.change_page('POWERON')
        self.add_child(n)
        
        n = MyToggle('iow:volume_low_256', 'iow:volume_mute_256')
        n.position = (w/2, 50)
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
            rows = int(cols / aspect_ratio)
            if len(self.children) <= rows * cols:
                break
            rows = int(cols / aspect_ratio + 0.5)
            if len(self.children) <= rows * cols:
                break
        
        for i in range(len(self.children)):
            c = i % cols
            r = int(i / cols)
            x = self.size.w / cols * (c + 0.5)
            y = self.size.h / rows * (r + 0.5)
            
            self.children[i].position = (x, self.size.h - y)
        
        
class RemBluePage(MyPage):
    def setup(self):
        self.color = (0, 0, 0.5, 0.5)
        self.z_position = 1
        
        self.panel = MyPanel(Size(300, 200), 'grey')
        self.panel.origin = self.panel.position = (300, 400)
        self.add_child(self.panel)

    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        print('blue')
        root.change_page('TV')

      
class RemRootScene(MyScene):
    def setup(self):
        self.disable_status()
        
        # for x in dir(ObjCInstance(self.view)):
        #   if x[-1:] != '_':
        #        print(x)
        
        self.page = None
        self.controller = controller.MyController(hostname)
        
        # self.background_color = '#222'
        w, h = self.size
        
        title = RemTitlebar("Yamaha", self.size, (0.7, 0.7, 0.7, 0.7))
        title.position = (w / 2, h - 50 / 2)
        self.add_child(title)
        
        self.power_off_scene = RemPowerOffScene()
        
        self.pages = dict()
        self.pages['POWERON'] = RemPowerOnPage(self.size)
        self.pages['BLUE'] = RemBluePage(self.size)
        self.pages['TV'] = RemTVPage(self.size)

        self.label = LabelNode('Yamaha')
        self.label.position = (0, 20)
        self.label.anchor_point = (0, 0)
        self.add_child(self.label)

        self.line2 = LabelNode('Yamaha')
        self.line2.position = (0, 40)
        self.line2.anchor_point = (0, 0)
        self.add_child(self.line2)

        self.change_page('POWERON')
        
    def touch_began(self, touch):
        self.label.text = repr(touch.location)
        handled = super().touch_began(touch)
        print('handled', handled)
        
    def disable_status(self):
        from objc_util import ObjCInstance
        ObjCInstance(self.view).statusLabel().alpha = 0
                
    def change_page(self, page_id):
        page = self.pages[page_id]
        print('current page', type(self.page).__name__)
        print('new page', type(page).__name__)
        if self.page is not None and self.page != page:
            self.page.run_action(
                Action.sequence(
                    Action.fade_to(0, 0.25),
                    Action.remove()
                )
            )
        self.page = page
        self.page.alpha = 0
        self.add_child(page)
        self.page.run_action(Action.fade_to(1, 0.25))
        
    def change_scene(self, scene):
        if self.presented_scene:
            self.dismiss_modal_scene()
            #self.presented_scene.run_action(Action.fade_to(0, 0.5, TIMING_EASE_OUT))
        
        # Fade in new scene
        scene.alpha = 0
        self.present_modal_scene(scene)
        scene.run_action(Action.fade_to(1, 0.25, TIMING_EASE_IN))
        

if __name__ == '__main__':
    root = RemRootScene()
    # orientation no longer really works
    run(root, orientation=LANDSCAPE)
