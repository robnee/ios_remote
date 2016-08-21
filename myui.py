'''Simple UI widgets built on top of Pythonista scene module
'''

from scene import *
import ui
import sound
import scene


class MyTarget:
    '''Touch target for UI. Gives feedback and optionally performs an action'''
    def __init__(self):
        self.touch = None
        self.action = None
        self.repeating = False
        
    def touch_began(self, touch):
        self.fade_down()
        self.start_repeat(touch)
        self.touch = touch

    def touch_moved(self, touch):
        if self.touch is not None:
            self.touch = touch
        
    def touch_ended(self, touch):
        self.fade_up()
        self.cancel_repeat()
        if self.touch is not None:
            self.dispatch()
        self.touch = None

    def touch_repeat(self, touch):
        # hackish way to detect expiration of this touch by asking the root
        # if this is still a touch in flight. if not fade up. Attempting
        # to mess with the action from inside a callback is fatal though.
        if touch.touch_id in self.scene.touches:
            if self.repeating:
                self.dispatch()
        elif self.touch is not None:
            self.touch = None
            self.fade_up()

    def dispatch(self):
        sound.play_effect('8ve:8ve-tap-simple')
        if self.action is not None:
            self.action.fire()

    def start_repeat(self, touch):
        self.cancel_repeat()
        self.run_action(
            Action.sequence(
                Action.wait(0.75),
                Action.repeat(
                    Action.sequence(
                        Action.call(lambda: self.touch_repeat(touch)),
                        Action.wait(0.20)
                    ),
                    25
                )
            ),
            'repeat'
        )
            
    def cancel_repeat(self):
        self.remove_action('repeat')

    def fade_down(self):
        self.run_action(
            Action.sequence(
                Action.fade_to(0.5, 0.05)
            )
        )

    def fade_up(self):
        if self.alpha < 1.0:
            self.run_action(
                Action.sequence(
                    Action.fade_to(1.0, 0.05)
                )
            )
 
    
class MyDispatch():
    '''Base class for collection of MyTarget classes. handles dispatch to targets'''
    def touch_began(self, touch):
        target = self.find_target(touch)
        if target:
            touch.location = target.point_from_scene(touch.location)
            target.touch_began(touch)
            return True  
        return False

    def touch_moved(self, touch):
        target = self.find_target(touch)
        if target:
            touch.location = target.point_from_scene(touch.location)
            target.touch_moved(touch)
            return True  
        return False
        
    def touch_ended(self, touch):
        target = self.find_target(touch)
        if target:
            touch.location = target.point_from_scene(touch.location)
            target.touch_ended(touch)
            return True  
        return False

    def find_target(self, touch):
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyDispatch) or isinstance(x, MyTarget):
                    return x     
        return None


class MyLabelButton(ShapeNode, MyTarget):
    '''Button by combining LabelNode with target handling'''
    def __init__(self, text, font, size=None, *args, **kwargs):
        MyTarget.__init__(self)
        
        self.label = LabelNode(text, font)
        self.add_child(self.label)

        if size is None: size = self.label.size
        
        path = ui.Path.rounded_rect(0, 0, size.w, size.h, size.w / 10)
        path.line_width = 0
        ShapeNode.__init__(self, path, *args, **kwargs)
        

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
        self.repeating = False
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

    def touch_moved(self, touch):
        MyDispatch.touch_moved(self, touch)
        
    def touch_ended(self, touch):
        MyDispatch.touch_ended(self, touch)
    
    def disable_status(self):
        from objc_util import ObjCInstance
        v = ObjCInstance(self.view)
        v.statusLabel().alpha = 0
            
    def hide_close(self, state=True):
        from objc_util import ObjCInstance
        v = ObjCInstance(self.view)
        for x in v.subviews():
            #if 'UIButton' in x.description():
            if str(x.description()).find('UIButton') >= 0:
                x.setHidden(state)
        

class MyPanel(ShapeNode, MyDispatch):
    '''A panel for grouping targets.  supports dispatch'''
    def __init__(self, size, fill_color):
        ShapeNode.__init__(self, fill_color=fill_color)
        self.set_size(size)
        
        self.anchor_point = (0, 0)
        
    def set_size(self, value):
        self.path = ui.Path.rounded_rect(0, 0, value.w, value.h, 10)
        self.path.line_width = 0
        self.size = value
