import unittest
import re

from hyperon import *
from common import interpret_until_result, Atomese, AtomspaceAtom

def interpret_and_print_results(target, kb, add_results_to_kb=False):
    output = ""
    while True:
        next = interpret_until_result(target, kb)
        if next == S('eos'):
            break
        print(next)
        output = output + str(next) + "\n"
        if add_results_to_kb:
            kb.add_atom(next)
    return output

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

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, 'blue\ngreen\nred\n')

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

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(make_from pottery clay)\n')

    def test_grounded_arithmetics(self):
        atomese = Atomese()

        kb = atomese.parse('''
            (= (foo $a $b) (* (+ $a $b) (+ $a $b)))
        ''')

        target = atomese.parse('''
            (foo 3 4)
            (+ 'Hello ' 'world')
        ''')

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, "'Hello world'\n49\n")

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

        output = interpret_and_print_results(target, kb, add_results_to_kb=True)
        self.assertEqual(output, '(= (Fritz frog) True)\n(= (Fritz green) True)\n')

    def test_frog_unification(self):
        atomese = Atomese()

        kb = atomese.parse('''
           (= (if True $then) $then)
           (= (frog $x) (and (croaks $x) (eat_flies $x)))
           (= (croaks Fritz) True)
           (= (eat_flies Fritz) True)
           (= (green $x) (frog $x))
        ''')

        target = atomese.parse('(if (green $x) $x)')

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, 'Fritz\n')

    def test_air_humidity_regulator(self):
        atomese = Atomese()

        kb = atomese.parse('''
           (= (if True $then) $then)
           (= (make $x) (if (makes $y $x) (start $y)))
           (= (make $x) (if (and (prevents (making $y) (making $x))
                                   (makes $z $y)) (stop $z)))

           (= (is (air dry)) (make (air wet)))
           (= (is (air wet)) (make (air dry)))
           (= (prevents (making (air dry)) (making (air wet))) True)
           (= (prevents (making (air wet)) (making (air dry))) True)

           (= (makes humidifier (air wet)) True)
           (= (makes kettle (air wet)) True)
           (= (makes ventilation (air dry)) True)
        ''')

        target = atomese.parse('(is (air dry))')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(stop ventilation)\n(start kettle)\n(start humidifier)\n')

        target = atomese.parse('(is (air wet))')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(stop kettle)\n(stop humidifier)\n(start ventilation)\n')

    # FIXME: segfault after this test is executed
    def _test_subset_sum_problem(self):
        atomese = Atomese()

        kb = atomese.parse('''
           (= (if True $then) $then)

           (= (bin) 0)
           (= (bin) 1)
           (= (gen 0) nil)
           (= (gen $n) (if (> $n 0) (:: (bin) (gen (- $n 1)))))

           (= (subsum nil nil) 0)
           (= (subsum (:: $x $xs) (:: $b $bs)) (+ (* $x $b) (subsum $xs $bs)))
        ''')

        target = atomese.parse('''(let $t (gen 3)
            (if (== (subsum (:: 3 (:: 5 (:: 7 nil))) $t) 8) $t))''')

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(:: 1 (:: 1 (:: 0 nil)))\n')

    def test_infer_function_application_type(self):
        atomese = Atomese()

        kb = atomese.parse('''
           (= (if True $then) $then)

           (= (: (apply $f $x) $r) (and (: $f (=> $a $r)) (: $x $a)))

           (= (: reverse (=> String String)) True)
           (= (: "Hello" String) True)
        ''')

        target = atomese.parse('(if (: (apply reverse "Hello") $t) $t)')

        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, 'String\n')

    def test_plus_reduces_Z(self):
        atomese = Atomese()

        kb = atomese.parse('''
           (= (eq $x $x) True)
           (= (plus Z $y) $y)
           (= (plus (S $k) $y) (S (plus $k $y)))
        ''')

        target = atomese.parse('(eq (+ 2 2) 4)')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, 'True\n')

        target = atomese.parse('(eq (+ 2 3) 4)')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(eq 5 4)\n')

        target = atomese.parse('(eq (plus Z $n) $n)')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, 'True\n')

        target = atomese.parse('(eq (plus (S Z) $n) $n)')
        output = interpret_and_print_results(target, kb)
        self.assertEqual(output, '(eq (S $n) $n)\n')


    def test_visit_kim(self):
        atomese = Atomese()
        kb = GroundingSpace()
        atomese.add_atom("kb", AtomspaceAtom(kb, "kb"))

        # it's questionable if the representation of (health-check Kim)
        # which can be interpreted as a functional call is correct,
        # but these tests pass for now
        program = '''
            (= (perform (visit $x)) (perform (lunch-order $x)))
            (= (perform (visit $x)) (perform (health-check $x)))

            (impl (is-achieved (visit $x))
                  (And (is-achieved (lunch-order $x)) (is-achieved (health-check $x))))

            (= (achieve $goal)
               (match kb (impl (is-achieved $goal)
                               (And (is-achieved $subgoal1) (is-achieved $subgoal2)))
                      (do $subgoal1 $subgoal2)))

            (= (achieve (health-check Kim)) True)
            (= (achieve (lunch-order Kim)) False)
            '''
        # (do $subgoal1 $subgoal2) --> (do (achieve $subgoal1) (achieve $subgoal2)))) --
        # -- will try to execute 'achieve' and produce (do True True) as output...

        atomese.parse(program, kb)

        # simple functional way to produce subgoals in target
        target = atomese.parse('(perform (visit Kim))')
        result = interpret_until_result(target, kb)
        # returned now as output because there is no further interpretation of this expression
        # it could be expanded further into subgoals or external actions
        self.assertEqual(repr(result), '(perform (health-check Kim))')
        # the next subgoal is produced in the consequent interpretation of the initial
        # nondeterministic expression
        result = interpret_until_result(target, kb)
        self.assertEqual(repr(result), '(perform (lunch-order Kim))')

        # Higher-order matching:
        # (visit Kim) -> $goal in (achieve $goal)
        # Kim -> $x in (impl (is-achieved (visit $x)) ...
        # $subgoal[1,2] <- (is-achieved ([lunch-order, health-check] Kim))
        # checking if such two-side unification works:
        target = atomese.parse('(achieve (visit Kim))')
        result = interpret_until_result(target, kb)
        self.assertEqual(repr(result), '(do (lunch-order Kim) (health-check Kim))')

        # Extending the program
        atomese.parse('(= (do $goal1 $goal2) (achieve $goal1))', kb)
        atomese.parse('(= (do $goal1 $goal2) (achieve $goal2))', kb)
        target = atomese.parse('(achieve (visit Kim))')
        # (achieve (visit Kim)) --> (do (lunch-order Kim) (health-check Kim))
        # --> (achieve (health-check Kim)) ... --> True
        result = interpret_until_result(target, kb)
        self.assertEqual(repr(result), 'True')

class SomeObject():

    def foo(self):
        print("foo called")

if __name__ == "__main__":
    unittest.main()
