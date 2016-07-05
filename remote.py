from scene import *
import ui
import sound
import scene
import controller

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
        if self.action != None:
            self.action()    

    def touch_repeat(self, touch):
        self.dispatch ()

    def touch_ended(self, touch):
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
        
        
class MyPanel(ShapeNode):
    def __init__(self, fill_color):
        ShapeNode.__init__(self, path = ui.Path.rounded_rect(0, 0, 400, 200, 10),
             fill_color=fill_color)
        self.anchor_point = (0, 0)
             
    def touch_began(self, touch):
        for x in self.children:
            #print('node frame:', x.frame)
            #print('node position:', x.position)
            #print('node origin:', x.frame.origin)
            #print('touch location:', touch.location)
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyButton) or isinstance(x, MyTarget):
                    x.touch_began(touch)
                    return
                    
    def touch_ended(self, touch):
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyTarget):
                    x.touch_ended(touch)
                    return
                    
class MyTitlebar(ShapeNode):
    def __init__(self, title, size, background_color):
        ShapeNode.__init__(self, path=ui.Path.rect(0, 0, size.w, size.h), fill_color=background_color)
        text = LabelNode(title)
        self.add_child(text)
        self.z_position = 5
                        
class MyScene (Scene):
    def setup(self):
        self.controller = controller.MyController()
        
        self.background_color = '#222'
        w, h = self.size
        
        title = MyTitlebar("Yamaha", Size(w, 50), (0.7, 0.7, 0.7, 0.7))
        title.position = (w / 2, h - 50/2)
        self.add_child(title)
        
        block = MyButton('❌', ('Helvetica',40))
        block.position = (w - 100, h - 50)
        self.add_child(block)

        self.label = LabelNode('Yamaha')
        self.label.position = (0, 20)
        self.label.anchor_point = (0, 0)
        self.add_child(self.label)

        self.line2 = LabelNode('Yamaha')
        self.line2.position = (0, 40)
        self.line2.anchor_point = (0, 0)
        self.add_child(self.line2)

        self.panel = MyPanel('grey')
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
        n.action = lambda : self.controller.put('@MAIN:VOL', 'Up')
        self.panel.add_child(n)

        n = MyImgButton('iow:chevron_down_256')
        n.position = (350, 50)
        n.action = lambda : self.controller.put('@MAIN:VOL', 'Down')
        self.panel.add_child(n)

    def touch_began(self, touch):
        #laser = SpriteNode('spc:LaserBlue9', position=self.ship.position, z_position=-1, parent=self)
        #laser.run_action(Action.sequence(Action.move_by(0, 1000), Action.remove()))
        self.label.text = repr(touch.location)
        for x in self.children:
            if x.frame.contains_point(touch.location):            
                if isinstance(x, MyPanel) or isinstance(x, MyButton):
                    self.line2.text = repr(x.point_from_scene(touch.location))
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_began(touch)
                    return
        
        # unhandled
        sound.play_effect('casino:CardSlide1')

    def touch_ended(self, touch):
        for x in self.children:
            if x.frame.contains_point(touch.location):
                if isinstance(x, MyPanel):
                    touch.location = x.point_from_scene(touch.location)
                    x.touch_ended(touch)
                    return
        
#view = SceneView()
#view.scene = MyScene()
#view.present('fullscreen', hide_title_bar=True)
run(MyScene(), LANDSCAPE)
