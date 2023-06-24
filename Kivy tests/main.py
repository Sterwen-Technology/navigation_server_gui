import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


class MyTest(BoxLayout):

    pass


class MyTestApp(App):

    def build(self):
        return MyTest()


if __name__ == '__main__':
    MyTestApp().run()
