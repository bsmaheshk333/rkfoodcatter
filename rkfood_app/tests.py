# from django.test import TestCase
#
# # Create your tests here.


input_str = "t#is is a #am#le #strin#"
# output = " this is a sample string
consonensts= "aaaaeeeeohsapirgout"

map_ = ['h', 's', 'p', 'g']

class A:
    def method(self):
        print("a class")

class B(A):
    def method(self):
        print("B class")
        super().method()


class C(B):
    def method(self):
        print("C class")
        super().method()

class D(B, C):
    def method(self):
        print("D class")
        super().method()


obj = D()
obj.method()

"""
d
b
c
"""
