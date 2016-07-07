'''
Home Theater Remote Control System
'''

from scene import *
import ui
import sound
import scene
import controller


hostname = 'none'


class MyTarget:
    def __init__(self):
        self.action = None
        self.repeat = True
        
    def touch_began(self, touch):
        # flash the button to notify press
        self.run_action(
            Action.sequence(
                Action.fade_to(0.5, 0.1),
                Action.fade_to(1.0, 0.2)
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
        sound.play_effect('8ve:8ve-tap-simple')
        if self.action is not None:
            self.action()
        
    def touch_repeat(self, touch):
        print('repeat')
        self.dispatch()

    def touch_ended(self, touch):
        print('ended')
        self.remove_action('repeat')


class MyButton(LabelNode, MyTarget):
    def __init__(self, text, font):
        MyTarget.__init__(self)
        LabelNode.__init__(self, text, font)


class MyImgButton(SpriteNode, MyTarget):
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
        

class MyDispatch():
    def touch_began(self, touch):
        print('MyDispatch.touch_began')
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyDispatch) or isinstance(x, MyTarget):
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_began(touch)
                    return True
                    
        return False
                    
    def touch_ended(self, touch):
        print('MyDispatch.touch_ended')
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyDispatch) or isinstance(x, MyTarget):
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_ended(touch)
                    return True
                    
        return False


class MyPanel(ShapeNode, MyDispatch):
    def __init__(self, size, fill_color):
        path = ui.Path.rounded_rect(0, 0, size.w, size.h, 10)
        path.line_width = 0
        ShapeNode.__init__(self, path=path, fill_color=fill_color)
        
        self.anchor_point = (0, 0)
             

class MyTitlebar(ShapeNode, MyDispatch):
    def __init__(self, title, size, background_color):
        ShapeNode.__init__(self, path=ui.Path.rect(0, 0, size.w, size.h),
                           fill_color=background_color)
        text = LabelNode(title)
        self.add_child(text)
        self.z_position = 1

        power = MyImgButton('iow:power_256')
        power.position = (-size.w/2 + 25, 0)
        power.action = lambda: root.power_scene()
        power.repeat = False
        power.size = (40, 40)
        self.add_child(power)

class MyScene(Scene, MyDispatch):
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

    def touch_ended(self, touch):
        MyDispatch.touch_ended(self, touch)
        
class MyBlueScene(MyScene):
    def setup(self):
        self.background_color = (0, 0, 0.5, 0.5)
        self.z_position = 1
        MyScene.setup(self)

    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        
        parent = self.presenting_scene
        if parent:
            parent.change_scene(parent.power_off_scene)
            
            
class MyPowerOffScene(MyScene):
    def setup(self):
        self.background_color = (0.5, 0, 0, 0.3)
        self.z_position = 1

        self.panel = MyPanel(Size(400, 300), 'grey')
        self.panel.origin = self.panel.position = (self.size.w/2, 500)
        self.add_child(self.panel)
        
        self.label = LabelNode('Yamaha')
        self.label.position = (self.size.w, 20)
        self.label.anchor_point = (0, 0)
        self.panel.add_child(self.label)
        
        MyScene.setup(self)
        
    def touch_began(self, touch):
        sound.play_effect('casino:ChipsStack4')
        
        parent = self.presenting_scene
        if parent:
            parent.change_scene(parent.blue_scene)

                     
class MyRootScene(MyScene):
    def power_scene(self):
        if not self.presented_scene:
            self.run_action(
                Action.sequence(
                    Action.wait(0.1),
                    Action.call(lambda: self.present_modal_scene(self.power_off_scene))
                )
            )

    def change_scene(self, scene):
        if self.presented_scene:
            self.dismiss_modal_scene()
            
        self.run_action(
            Action.sequence(
                Action.wait(0.1),
                Action.call(lambda: self.present_modal_scene(scene))
            )
        )
  
    def setup(self):
        # disable stdout overlay
        from objc_util import ObjCInstance
        ObjCInstance(self.view).statusLabel().alpha = 0
        
        #for x in dir(ObjCInstance(self.view)):
        #   if x[-1:] != '_':
        #        print(x)
        
        self.controller = controller.MyController(hostname)
        
        #self.background_color = '#222'
        w, h = self.size
        
        title = MyTitlebar("Yamaha", Size(w, 50), (0.7, 0.7, 0.7, 0.7))
        title.position = (w / 2, h - 50/2)
        self.add_child(title)
        
        self.power_off_scene = MyPowerOffScene()
        self.blue_scene = MyBlueScene()

        self.label = LabelNode('Yamaha')
        self.label.position = (0, 20)
        self.label.anchor_point = (0, 0)
        self.add_child(self.label)

        self.line2 = LabelNode('Yamaha')
        self.line2.position = (0, 40)
        self.line2.anchor_point = (0, 0)
        self.add_child(self.line2)

        self.panel = MyPanel(Size(500, 200), 'grey')
        self.panel.origin = self.panel.position = (200, 500)
        self.add_child(self.panel)

        block = MyButton('▶️', ('Helvetica', 80))
        block.position = (50, 50)
        self.panel.add_child(block)
        
        n = MyButton('🔵', ('Helvetica', 80))
        n.position = (125, 50)
        self.panel.add_child(n)
        
        n = MyToggle('iow:volume_low_256', 'iow:volume_mute_256')
        n.position = (200, 50)
        n.action = lambda: sound.play_effect('ui:switch15')
        self.panel.add_child(n)

        n = MyImgButton('iow:chevron_up_256')
        n.position = (275, 50)
        n.action = lambda: self.controller.put('@MAIN:VOL', 'Up')
        self.panel.add_child(n)

        n = MyImgButton('iow:chevron_down_256')
        n.position = (350, 50)
        n.action = lambda: self.controller.put('@MAIN:VOL', 'Down')
        self.panel.add_child(n)

    def touch_began(self, touch):
        self.label.text = repr(touch.location)
        super().touch_began(touch)

    def touch_ended(self, touch):
        print ('MyRootScene.touch_ended')
        super().touch_ended(touch)

root = MyRootScene()       
run(root, LANDSCAPE)
