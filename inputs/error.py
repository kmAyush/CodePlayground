import traceback
class Animal:
    def __init__(self, name, sound):
        self.name = name
        self.sound = sound

    def speak(self):
        return self.name + " says " + self.sound

try:
    dog = Animal("Dog", "Woof")
    print(dog1.speak())
except Exception as e:
    traceback.print_exc()
    print("Error:",e)
