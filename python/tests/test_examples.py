import unittest
import re

from hyperon import *
from common import interpret_until_result, Atomese

def interpret_and_print_results(target, kb, add_results_to_kb=False):
    while True:
        next = interpret_until_result(target, kb)
        if next == S('eos'):
            break
        print(next)
        if add_results_to_kb:
            kb.add_atom(next)

class ExamplesTest(unittest.TestCase):

    def test_show_all_color_names(self):
        atomese = Atomese()

        kb = atomese.parse('''
            (isa red color)
            (isa green color)
            (isa blue color)
        ''')

        atomese.add_atom("kb", ValueAtom(kb))
        target = atomese.parse('(match kb (isa $color color) $color)')

        interpret_and_print_results(target, kb)

    def test_create_semantic_triple(self):
        atomese = Atomese()

        kb = atomese.parse('''
            (obj make pottery)
            (from make clay)
        ''')

        atomese.add_atom("kb", ValueAtom(kb))
        target = atomese.parse('''
            (match kb (obj $verb $var0)
                (q match kb (from $verb $var1) (make_from $var0 $var1)))
        ''')

        interpret_and_print_results(target, kb)

    def test_grounded_arithmetics(self):
        atomese = Atomese()

        kb = atomese.parse('''
            (= (foo $a $b) (* (+ $a $b) (+ $a $b)))
            (= (foo $a $b) (* (+ $a $b) (+ $a $b)))
        ''')

        target = atomese.parse('''
            (foo 3 4)
            (+ 'Hello ' 'world')
        ''')

        interpret_and_print_results(target, kb)

    def test_grounded_functions(self):
        atomese = Atomese()

        atomese.add_atom("obj", ValueAtom(SomeObject()))
        target = atomese.parse('(call:foo obj)')

        interpret_and_print_results(target, GroundingSpace())

    def test_frog_reasoning(self):
        atomese = Atomese()

        kb = atomese.parse('''
            (= (if True $then $else) $then)
            (= (if False $then $else) $else)
            (= (Fritz croaks) True)
            (= (Tweety chirps) True)
            (= (Tweety yellow) True)
            (= (Tweety eats_flies) True)
            (= (Fritz eats_flies) True)
        ''')

        target = atomese.parse('''
            (if ($x frog) (= ($x green) True) nop)
            (if (and ($x croaks) ($x eats_flies)) (= ($x frog) True) nop)
        ''')

        interpret_and_print_results(target, kb, add_results_to_kb=True)

    def test_air_humidity_regulator(self):
        Logger.setLevel(Logger.DEBUG)
        atomese = Atomese()

        kb = atomese.parse('''
            (= (if True $then) $then)
            (= (make $x) (if ($y makes $x) (start $y)))
            (= (make $x) (if (and ((making $y) prevents (making $x)) ($z
                           makes $y)) (stop $z)))

            (= (too dry) (make (air wet)))
            (= (too wet) (make (air dry)))
            (= ((making (air dry)) prevents (making (air wet))) True)
            (= ((making (air wet)) prevents (making (air dry))) True)

            (= (humidifier makes (air wet)) True)
            (= (kettle makes (air wet)) True)
            (= (ventilation makes (air dry)) True)
        ''')

        target = atomese.parse('(too dry)')
        target = atomese.parse('(too wet)')

        interpret_and_print_results(target, kb)

class SomeObject():

    def foo(self):
        print("foo called")

if __name__ == "__main__":
    unittest.main()
