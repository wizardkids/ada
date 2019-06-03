"""
ada v2.3.py

Richard E. Rawson
2019-05-28

Command line RPN calculator that performs a variety of common functions.

NOTE:
1. version number appears in three places:
    -- header
    -- about()
    -- if __name__ == '__main__'

2. Some functions print out the dictionaries (at the end of this file) to provide lists of available functions accessible to the user, along with a snippet of information for each command. Many of the docStrings in this file are also accessible (via "help") as a means of providing extended information about each command.



change log:
    v 1.9
        -- organize (and bookmark) functions into categories
    v 2.1
        -- add memory stack functions
        -- add {mem} as a global dictionary
        -- add M+, M-, MR, and ML to {commands}, matching docString to description in {commands}
        -- add {mem} to function arguments for RPN() and process_item() 
        -- add ability to access memory stack in process_items()
        -- now accepts only lower case commands, except for F, C, M+, M-, MR, and ML
        -- fixed order or arguments in stack = temperature_conversion(item, stack) to stack = temperature_conversion(stack, item)
        -- reverse order of commands and math operations in print_user_functions()
        -- add an interactive help
        -- a multitude of fixes

    v 2.2
        -- add capability to save to and retrieve mathematical expressions from constants.json. Once retrieved, the expression is executed and the result placed on the stack.

"""

import json
import math
import operator
import random
import statistics
import textwrap
from inspect import getmembers, isfunction
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from sys import modules


# todo -- When I run < ue trial> with 3 and 4 on the stack, the 3 an 4 are not destroyed, but are moved to z: and y: and the result, 7, is put in x:

# ! version 2.3...

# todo -- add the ability to read in a .csv file, checking that it contains numbers only on each line, which will also check that there are no headers since ada would not know what to do with them.
    # * the question is, beyond summary stats, what else would you do with a stack full of number, that would not require numpy or pandas?
    # * or... maybe pandas would offer an easy way to get something useful from a list of numbers???

# todo -- thoroughly test all fxns


# MAIN CALCULATOR FUNCTION ====================

def RPN(stack, dict, lastx_list, mem, settings, tape, user_exp):
    """
    Main function that processes user's input and does initial processing. This means that some inputs can be handled easily, but most will require further processing by process_item() which will return a [list] of individual items.
    """

    while True:
        quit = False

        try:
            with open("constants.json") as file:
                dict = json.load(file)
        except FileNotFoundError:
            dict = {}
        
        if settings['show_tape'] == 'Y':
            print_tape(stack, tape)
        print_register(stack)

        # generate the menu
        print()
        for i in range(0, len(menu), 4):
            m = ''.join(menu[i:i+4])
            print(m)

        # get the command line entry
        entered_value = input('\n').lstrip().rstrip()
        
        # make sure parentheses are balanced before proceeding
        lst = list(entered_value)
        if lst.count('(') - lst.count(')') != 0:
            print('Unbalanced parentheses.')
            continue

        # add the current expression to the tape
        tape.append(entered_value)

        # if the user wants a user-defined expression, then they entered "user_expr" or "ue"
        if entered_value[0:9] == 'user_expr' or entered_value[0:2] == 'ue':
            item = entered_value[10:] if entered_value == 'user_expression' else entered_value[3:]
            entered_value = get_user_expression(item)


        # if <ENTER> alone was pressed, duplicate the x value on the stack and then <<continue>>
        if len(entered_value) == 0:
            x = stack[0]
            stack.insert(0, x)
            continue

        # if the entered_value begins with a '#', then it's a hex number; special handling
        elif entered_value[0] == '#':
            # then this is a hex number to be converted to rgb
            hex_to_rgb(stack, entered_value)
        
        # else, we're going to have to parse what the user entered
        else:
            # put each "entity" in entered_value into a list item
            entered_list = parse_entry(entered_value)

            ndx = 0
            while ndx < len(entered_list):

                item = entered_list[ndx]

                # the first 'if' statement allow for 
                # shortcut commands that are not in any of the other {}
                if item in shortcuts.keys():
                    if item == 'q':
                        quit = True
                    elif item == 'h':
                        try:
                            help_fxn(stack, entered_list[ndx+1])
                            ndx += 1
                        except:
                            # h by itself:
                            print('='*45)
                            print('For help with individual commands, type:')
                            print('\nh [command]\n', sep='')
                            print('where [command] is any command or operation.', sep='')
                            print('='*45)
                    else:
                        operation = shortcuts[item][0]
                        stack = operation(stack)

                # process all items except shortcuts and things that start with '('
                elif item != '(' and item not in shortcuts.keys():
                    # settings has to be handled differently
                    if item == 'set':
                        settings = calculator_settings(settings)
                    else:
                        stack, lastx_list, tape = process_item(stack, dict, lastx_list, mem, settings, tape, item)
                    ndx += 1
                    continue
                
                # if '(', then this is the start of a group
                elif item == '(':
                    while item != ')':
                        stack, lastx_list, tape = process_item(
                            stack, dict, lastx_list, mem, settings, tape, item)
                        ndx += 1
                        if ndx < len(entered_list):
                            try:
                                item = entered_list[ndx]
                            except:
                                pass
                        continue

                else:
                    pass

                ndx += 1

        if quit:
            print('\nEnd program.\n')
            return None

    return stack

# EXPRESSION EVALUATION FUNCTIONS ====================

def process_item(stack, dict, lastx_list, mem, settings, tape, item):
    """
    Process an item from [entered_list]. Return a modified [stack] (or modified {settings}).
    """

    # if it's a '(' or ')', the start or end of a group
    if item in ['(', ')']:
        pass

    # if item is a user-defined constant
    elif item in dict.keys():
        stack.insert(0, dict[item][0])

    # if item is a float
    elif type(item) == float:
        stack.insert(0, item)
        # save this item as lastx
        lastx_list = [lastx_list[-1]]
        lastx_list.append(stack[0])

    # if item is a math operator only requiring x
    elif item in op1:
        stack = math_op1(stack, item)

    # if item is a math operator requiring both x and y
    elif item in op2:
        stack = math_op2(stack, item)

    # if item is a named constant in {constants}
    # elif item in constants:
    #     pass

    # if operator is in {commands} or {shortcuts}
    elif item in commands or item in shortcuts or item in constants:

        # default is operation(stack)
        # these are items that have to be handled differently
        if item in commands:
            operation = commands[item][0]
        elif item in shortcuts:
            operation = shortcuts[item][0]
        elif item in constants:
            stack.insert(0, constants[item][0])
        if item == 'alpha':
            get_hex_alpha(stack)
        elif item == 'com':
            print_commands()
        elif item == 'con':
            print_constants()
        elif item == 'usercon':
            print_dict()
        elif item == 'help':
            help(stack)
        elif item == 'lastx':
            stack = operation(stack, lastx_list)
        elif item == 'list_alpha':
            list_alpha()
        elif item == 'man':
            manual()
        elif item == 'math':
            print_math_ops()
        elif item == 'M+':
            mem = mem_add(stack, mem)
        elif item == 'M-':
            mem = mem_sub(stack, mem)
        elif item == 'MR':
            mem = mem_recall(stack, mem)
        elif item == 'ML':
            mem = mem_list(stack, mem)
        elif item == 'short':
            print_shortcuts()
        elif item == 'set':
            settings = operation(settings)
            return settings
        elif item == 'stats':
            stats(stack)
        elif item == 'tape':
            tape = print_tape(stack, tape)
        elif item == 'user':
            define_constant(stack)
        else:
            if item not in constants:
                stack = operation(stack)

    # any unrecognized operation (a garbage entry)
    # is ignored and program simply continues...
    else:
        print('='*45)
        print('Unknown command.')
        print('='*45)

    return stack, lastx_list, tape


def parse_entry(entered_value):
    """
    Put each distinct element (character/operator/number) of the user's entered_value into a list.
    Return entered_list to RPN_stack().
    """

    data, j, entered_list, s = [], 0, [], ''

    # if the entered values is not a single key in {op1} or {op2}...
    if not (entered_value in op1.keys() or entered_value in op2.keys()):
        ndx = -1
        while True:

            ndx += 1
            if ndx >= len(entered_value):
                break

            # if it's an open or a closed parenthesis
            if entered_value[ndx] in ['(', ')']:
                s = entered_value[ndx]

            # if it's a number, gather all the following digits into one string
            elif entered_value[ndx] in digits or entered_value[ndx] == '-' or entered_value[ndx] == '.':
                while entered_value[ndx] in digits or entered_value[ndx] == '-' or entered_value[ndx] == '.':
                    s += entered_value[ndx]
                    try:
                        if entered_value[ndx+1] in digits or entered_value[ndx+1] == '-' or entered_value[ndx+1] == '.':
                            ndx += 1
                        else:
                            break
                    except IndexError:
                        break

            # if it's a alpha character, gather all the following characters into one string
            elif entered_value[ndx] in letters:
                while entered_value[ndx] in letters:
                    s += entered_value[ndx]
                    try:
                        if entered_value[ndx+1] in lower_letters:
                            ndx += 1
                        elif entered_value[ndx] == 'M' and entered_value[ndx+1] in ['+', '-', 'L', 'R']:
                            s += entered_value[ndx+1]
                            ndx += 1
                            break
                        else:
                            break
                    except IndexError:
                        break

            # if it's a (single character) math operator
            elif entered_value[ndx] in op2.keys() or entered_value[ndx] == '!':
                if s == '-':
                    break
                s += entered_value[ndx]

            # if item is a register on the stack, replace with stack value
            if s in ['x:', 'y:', 'z:', 't:']:
                s = str(stack[0]) if s == 'x:' else s
                s = str(stack[1]) if s == 'y:' else s
                s = str(stack[2]) if s == 'z:' else s
                s = str(stack[3]) if s == 't:' else s

            data.append(s)
            s = ''

    else:
        entered_list.append(entered_value)

    # convert numbers to floats and strip out empty elements or elements with punctuation (e.g., commas, as in, comma delimited number sequences)
    for i in data:
        if i in [',', ';', ':']:
            i = ' '
        if i.rstrip() or i in ['(', ')']:
            try:
                entered_list.append(float(i))
            except:
                entered_list.append(i)

    return entered_list


def print_register(stack):
    """
    Print the stack register.
    """

    stack_names = [' x', ' y', ' z', ' t']
    print()

    # stack must always have at least 4 elements
    while len(stack) < 4:
        stack.insert(len(stack), 0.0)

    for register in range(3, -1, -1):
        # get the number of decimals from {settings}
        dp = settings['dec_point']
        delimiter = settings['delimiter']
        if (stack[register] > 1e7 or
                stack[register] < -1 * 1e6) and (stack[register] != 0.0):
            # switch to scientific notation
            fs = ('{:'+ delimiter + '.0' + dp + 'e}').format(stack[register])
        else:
            # switch to regular number notation
            fs = ('{:' + delimiter + '.0' + dp + 'f}').format(stack[register])

        # line up decimal points
        p = 11 + len(fs) - fs.find('.')

        print(stack_names[register], ':',
              ('{:>' + str(p) + '}').format(fs), sep='')
    return stack


# PRINT FUNCTIONS (MANUAL) ====================

def manual():
    """
    Menu to access parts of the manual.
    """
    txt, line_width = ' MANUAL ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')
    print(
            '<com>mands and stack operations\n', \
            '<math> operations\n'
            '<short>cuts\n', \
            '<con>stants/conversions\n', \
            '<user>-defined <con>stants', \
            sep='')
    print('='*line_width)
    return


def print_commands():
    """
    List all commands, including those that manipulate the stack.
    """
    # print all the keys in {shortcuts}
    txt, line_width = ' COMMANDS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in commands.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')

    return


def print_math_ops():
    """
    List all math operations.
    """
    # print all the keys, values in {op1} and {op2}
    txt, line_width = ' MATH OPERATIONS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in op1.items():
        print('{:>13}'.format(k), '|', v[1])

    for k, v in op2.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')

    return


def print_shortcuts():
    """
    List shortcut functions.
    """
    # print all the keys, values in {shortcuts}
    txt, line_width = ' SHORTCUTS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in shortcuts.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')
    return


def print_constants():
    """
    List constants and conversions.
    """
    # print all the keys, values in {constants}
    txt, line_width = ' CONSTANTS & CONVERSIONS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in constants.items():
        print('{:>13}'.format(k), '|', v[0], ": ", v[1], sep='')

    print('='*line_width, sep='')
    return


def print_dict():
    """
    List user-defined constants, if they exist.\n\nType:\n\nuser\n\nto edit user-defined constants.
    """
    # print all the keys, values in {dict}
    try:
        with open("constants.json") as file:
            dict = json.load(file)
    except FileNotFoundError:
        dict = {}

    txt, line_width = ' USER-DEFINED CONSTANTS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in dict.items():
        print(k, ': ', v[0], ' ', v[1], sep='')

    print('='*line_width, sep='')


def print_all_functions(stack, dict):
    """
    All commands and math operations. This function is not used, except by the developer.
    """

    # strategy: only get docstrings from things NOT in this list; this will be all the fxns that the user can use
    module_functions = ['RPN', 'process_item', 'parse_entry','print_register', 'calculator_settings', 'print_all_functions', 'print_commands', 'help', 'help_1', 'help_2', 'math_op1', 'math_op2', 'wrap_text']

    func_name = ''   
    func_list = []
    print('='*14, ' MATH OPERATIONS ', '='*14, sep='')

    txt, line_width = ' MATH OPERATIONS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for i in getmembers(modules[__name__],
                        predicate=lambda f: isfunction(f) and f.__module__ == __name__):
        func = i[0]
        fnd = False
        if func in module_functions:
            continue
        for k, v in op2.items():
            if v[0].__name__ == func:
                fnd = True
                func_name = k
                docString = v[1]
                break
        if not fnd:
            continue

        print('{:>8}'.format(func_name), ' | ', sep='', end='')
        wrapper = textwrap.TextWrapper(width=line_width)
        explanation = wrapper.wrap(text=docString)
        for element in explanation:
            print(element)

    func_name = ''
    func_list = []
    for i in getmembers(modules[__name__],
                        predicate=lambda f: isfunction(f) and f.__module__ == __name__):
        func = i[0]
        fnd = False
        if func in module_functions:
            continue
        for k, v in op1.items():
            if v[0].__name__ == func:
                fnd = True
                func_name = k
                docString = v[1]
                break
        if not fnd:
            continue

        print('{:>8}'.format(func_name), ' | ', sep='', end='')
        wrapper = textwrap.TextWrapper(width=line_width)
        explanation = wrapper.wrap(text=docString)
        for element in explanation:
            print(element)

    func_name = ''
    func_list = []
    txt, line_width = ' COMMANDS ', 45
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for i in getmembers(modules[__name__],
                        predicate=lambda f: isfunction(f) and f.__module__ == __name__):
        func = i[0]
        fnd = False
        if func in module_functions:
            continue
        for k, v in commands.items():
            if v[0].__name__ == func:
                fnd = True
                func_name = k
                docString = v[1]
                break
        if not fnd:
            continue

        print('{:>8}'.format(func_name), ' | ', sep='', end='')
        wrapper = textwrap.TextWrapper(width=line_width)
        explanation = wrapper.wrap(text=docString)
        for element in explanation:
            print(element)
    return stack


# CALCULATOR SETTINGS ====================

def calculator_settings(settings):
    """
    Access and edit calculator settings. You can:\n\n(1) change the number of decimals that display in the stack. Example: 8p will change stack to show 8 decimal places\n(2) turn the thousands separator on or off\n(3) show the tape, updated after each expression.
    """
    while True:
        # print the current settings
        print('\n', '='*13, ' CURRENT SETTINGS ', '='*13, sep='')
        for k, v in settings.items():
            if k == "dec_point":
                print('Decimal points:', v)
            elif k == 'delimiter':
                if settings['delimiter'] == '':
                    print('     Delimiter: ', 'none', sep='')
                else:
                    print('     Delimiter: ', ',', sep='')
            elif k == 'show_tape':
                print('     Show tape: ', v)
            else:
                pass
        print('='*45)

        # print a menu of setting options
        s = input(
            "\nSet decimal <p>oint \
            \nSet thousands <d>elimiter \
            \nShow <t>ape \
            \n<E>xit\n")
        # if not s:
        #     break

        # parse the user's menu choice
        if s[-1] == 'p' or s[0] == 'p':
            # usage example: enter <<8p>> to set decimal points to 8 places
            # entering <<map>> or <<pee>> generates usage help
            # entering anything else simply skips this
            try:
                if s[-1] == 'p':
                    settings['dec_point'] = str(int(s[0:-1]))
                else:
                    settings['dec_point'] = str(int(s[1:]))

            except:
                print('Usage: [number decimal points][p]')

        elif s.strip().lower() == 'd':
            delimiter = input("Thousands separator ('none' or ','): ")
            if delimiter.strip().lower() == 'none':
                settings['delimiter'] = ''
            else:
                settings['delimiter'] = ','
        elif s.strip().lower() == 't':
            tape = input('Show tape persistently? (Y/N): ') 
            if tape.strip().upper() == 'Y':
                settings['show_tape'] = 'Y'
            else:
                settings['show_tape'] = 'N'
        else:
            pass

        # print the new settings
        print('\n', '='*15, ' NEW SETTINGS ', '='*15, sep='')
        for k, v in settings.items():
            if k == "dec_point":
                print('Decimal points:', v)
            elif k == 'delimiter':
                if settings['delimiter'] == '':
                    print('     Delimiter: ', 'none', sep='')
                else:
                    print('     Delimiter: ', ',', sep='') 
            elif k == 'show_tape':
                print('     Show tape: ', v)
            else:
                pass
        print('='*45)

        if s.lower() == 'e' or s.lower() == 'exit' or not s:
            break
            
    return settings


# CALCULATOR FUNCTIONS ====================

def about(stack):
    """
    Information about the author and product.
    """
    print('='*45, "\nada - an RPN calculator\n", 'v2.3\n',
          'python: 3.7\n', 'date: 2019-05-27\n', sep='')
    var = 'ada is named after Ada Lovelace (1815–1852), whose achievements included developing an algorithm showing how to calculate a sequence of numbers, forming the basis for the design of the modern computer. It was the first algorithm created expressly for a machine to perform.'

    wrapper = textwrap.TextWrapper(width=45)
    explanation = wrapper.wrap(text=var)
    for element in explanation:
        print(element)
    print('='*45)
    return stack


def clear(stack):
    """
    Clear all elements from the stack.
    """
    stack, entry_value = [0.0, 0.0, 0.0, 0.0], ''
    return stack

# === MATH OPERATORS =====

def log(stack):
    """
    Returns the log(10) of the x value.\n\nExample: 100 log --> x: 2, since 10^2 = 100.
    """
    x = stack[0]
    stack[0] = math.log10(x)
    return stack


def ceil(stack):
    """
    Returns to ceiling, the next higher integer, of x.\n\nExample: 6.3->7
    """
    x = stack[0]
    stack[0] = math.ceil(x)
    return stack


def floor(stack):
    """
    Returns the floor, the next lower integer, of x.\n\nExample: 6.9->6
    """
    x = stack[0]
    stack[0] = math.floor(x)
    return stack


def factorial(stack):
    """
    x factorial\n\nExample (1):\n4 factorial --> x: 24\n\nExample (2)\n4 ! --> x: 24\n\n Note that example (2) uses a shortcut. To list shortcuts, type: short
    """
    x = stack[0]
    stack[0] = math.factorial(x)
    return stack


def negate(stack):
    """
    Negative of x\n\nExample (1):\n4 negate --> x: -4\n\nExample (2)\n4 n --> x: -4\n\nNote that example (2) uses a shortcut. To list shortcuts, type: short
    """
    x = stack[0]
    stack[0] = operator.neg(x)
    return stack


def sin(stack):
    """
    sin(x) -- x must be radians
    """
    x = stack[0]
    stack[0] = math.sin(x)
    return stack


def cos(stack):
    """
    cos(x) -- x must be radians
    """
    x = stack[0]
    stack[0] = math.cos(x)
    return stack


def tan(stack):
    """
    tan(x) -- x must be radians
    """
    x = stack[0]
    stack[0] = math.tan(x)
    return stack


def asin(stack):
    """
    asin(x) -- x must be radians
    """
    x = stack[0]
    stack[0] = math.asin(x)
    return stack


def acos(stack):
    """
    acos(x) -- x must be radians
    """
    x = stack[0]
    stack[a0] = math.acos(x)
    return stack


def atan(stack):
    """
    atan(x) -- x must be radians
    """
    x = stack[0]
    stack[0] = math.atan(x)
    return stack


def pi(stack):
    """
    Puts the value of pi on the stack
    """
    x = stack[0]
    stack[0] = math.pi
    return stack


def deg(stack):
    """
    Convert x value from radians to degrees
    """
    stack[0] = math.degrees(stack[0])
    return stack


def rad(stack):
    """
    Convert x value from degrees to radians
    """
    stack[0] = math.radians(stack[0])
    return stack


def absolute(stack):
    """
    Put the absolute value of x on the stack.
    """
    x = stack[0]
    stack[0] = abs(x)
    return stack


def random_number(stack):
    """
    Generate a random integer between y (exclusive) and x (inclusive).\n\nExample: 1 100 rand --> x: 43 (or some random number)
    """
    ri = random.randint(int(stack[1]), int(stack[0]))
    stack.insert(0, ri)
    return stack


def add(stack):
    """
    y + x\n\nExample 4 3 + --> x: 7
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, x + y)
    return stack   


def sub(stack):
    """
    y - x\n\nExample: 4 3 - --> x: 1
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y - x)
    return stack


def mul(stack):
    """
    y * x\n\nExample: 5 3 * --> x: 15
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y * x)
    return stack   


def truediv(stack):
    """
    y / x\n\nExample: 12 3 / --> x: 4\n\nNote: division by zero will generate an error.
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y / x)
    return stack


def mod(stack):
    """
    Modulus: remainder from division.\n\nExample (1): 5 2 % --> x: 1\n\nExample (2): 4 2 % --> x: 0\n\nNote: A useful fact is that only even numbers will result in a modulus of zero.
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y % x)
    return stack


def pow(stack):
    """
    y to the power of x, or y ** x\n\nExample: 10 2 ^ --> x: 100
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y ** x)
    return stack


def math_op1(stack, item):
    """
    A variety of math operations on the x value.
    """
    if stack[0] < 0 and item == '!':
        print('='*45)
        print('No factorial computation on a negative number.')
        print('='*45)

    operation = op1[item][0]
    stack = operation(stack)

    return stack


def math_op2(stack, item):
    """
    Add, subtract, multiply, divide, modulus, power.
    """
    if item == '/' and stack[0] == 0:
            print('='*45)
            print('Cannot divide by zero.')
            print('='*45)
    else:
        operation = op2[item][0]
        stack = operation(stack)
    return stack


# === NUMBER SYSTEM CONVERSIONS =====

def convert_to_decimal(stack):
    """
    Convert x from binary to decimal. Puts decimal value on stack.\n\nExample: 1000 dec --> x: 8
    """
    print()
    stack[0] = int('0b'+str(int(stack[0])), 2)
    print()
    return stack


def convert_to_binary(stack):
    """
    Convert x to binary. Binary value is a sting so it is reported as a string, and not placed on the stack.\n\nExample: 8 bin --> "0b1000"\n\nNote: the x value remains on the stack.
    """
    print('='*45)
    print(bin(int(stack[0])))
    print('='*45)
    return stack

# === USER-DEFINED CONSTANTS FUNCTIONS ====


def define_constant(stack):
    """
    Define, edit, or delete a user-defined constant. Constants are saved to file and are retrieved automatically when the calculator starts. Cannot redefine system names (e.g., "swap").\n\nType:\n\nusercon\n\nto list the current user-defined constants.
    """
    try:
        with open("constants.json") as file:
            dict = json.load(file)
    except:
        dict = {}

    while True:
        name, value, description = '', '', ''
        print('\n', '='*10, ' USER-DEFINED CONSTANTS ', '='*11, sep='')
        for k, v in dict.items():
            print(k, ': ', v[0], ' ', v[1], sep='')
        print('='*45)
        while True:
            name = input("Name of constant/conversion: ")

            # check to see if there are any uppercase letters: ada can't handle them.
            upper = False
            for i in range(len(name)):
                if name[i] in ascii_uppercase:
                    print('Cannot use uppercase letters in a name.')
                    upper = True
            if upper:
                continue

            # if the constant already exists, edit or delete it
            if name in dict.keys():
                print("\nEnter new value to redefine ", name, ".", sep='')
                print('Enter no value to delete ', name, ".", sep='')
            # since '' exists in some of the dictionaries, but is meaningless,
            # then test for name = '' separately
            elif not name:
                pass
            elif name in op1.keys() or \
                    name in op2.keys() or \
                    name in constants.keys() or \
                    name in commands.keys() or \
                    name in shortcuts.keys() or \
                    name in alpha.keys():
                print(
                    '\n', '='*45, '\nName already in use. Choose another.\n', '='*45, sep='')
                continue

            # if you entered a name, get a value
            if name:
                while True:
                    value = input("Value of " + name + ': ')
                    if value != '' and value[0:4] != 'exp:':
                        try:
                            value = float(value)
                            break
                        except:
                            print("Value must be a valid float or integer.")
                            continue
                    elif value[0:4] == 'exp:':
                        value = value[4:].strip()
                        break
                    else:
                        break

            # if you enter no name and no value, then exit...
            if not name and value == '':
                break

            # if you gave a name, but enter no value, then offer to delete name
            if name:
                if name in dict.keys() and value == '':
                    ok_delete = input('Delete ' + name + '? (Y/N) ')
                    if ok_delete.upper() == 'Y':
                        del dict[name]
                    break
                elif not name in dict.keys() and value == '':
                    print('\nWhen you enter no value, it is presumed you want\n',
                          'to delete ', name, ' However, no such name exists.\n', sep='')
                else:
                    pass

            # if you entered a name and a value, get a description
            if name and value != '':
                description = input("Description: ")
                break

        # if you entered a name and a value (description is optional), update {dict}
        if name and value != '':
            dict.update({name: (value, description)})

        if not name and value == '':
            break

        repeat = ''
        while repeat.upper() not in ['Y', 'N']:
            repeat = input("Add or edit another constant? (Y/N): ")
        if repeat.upper() == 'N':
            break

    with open('constants.json', 'w+') as file:
        file.write(json.dumps(dict, ensure_ascii=False))

    print('\n', '='*10, ' USER-DEFINED CONSTANTS ', '='*11, sep='')
    for k, v in dict.items():
        print(k, ': ', v[0], ' ', v[1], sep='')
    print('='*45)

    return dict


def get_user_expression(item):
    """
    Get a user-defined expression from the file containing user-defined constants. Execute the expression and place the result on the stack. This operation is particularly useful if you need to reuse a complicated expression with different stack values, making this a rudimentary programmable calculator. \n\nUsage:\n\n(1) Type:\n\nuser\n\nto create and save an expression. Use x:, y:, z:, t: in your expression to refer to specific registers in the stack. NOTE: Keep in mind that the stack contents change as operations are executed. See example below.\n\n(2) To use your expression, put any necessary values on the stack, then...\n\n(3) Type:\n\nue or user_exp [expression name]\n\nto run the named user expression.\n\nExample:\n\n(x: y: +) y: *\n\n-- Put the following values on the stack.\n
 z:          7.0000
 y:          3.0000
 x:          1.0000\n
-- When the expression is run, the + operator adds x: and y:. y: is removed and x: is replace with the result: 4. z: drops down to the y: register\n
 z:          0.0000
 y:          7.0000
 x:          4.0000\n
-- Then the current x: and y: are multiplied and the result, 28, is put in the x: register.\n
 z:          0.0000
 y:          0.0000
 x:         28.0000\n
NOTE: The non-obvious point is that, in an expression, the registers (e.g., "x:") are not variable names, but refer to the stack at THAT point in the expression's execution.
    """
    try:
        with open("constants.json") as file:
            dict = json.load(file)
    except:
        dict = {}

    user_exp = ''
    if not dict:
        print('No expressions available.')
    elif item not in dict.keys():
        print('\n', '='*10, ' USER-DEFINED CONSTANTS ', '='*11, sep='')
        for k, v in dict.items():
            print(k, ': ', v[0], ' ', v[1], sep='')
        print('='*45)
        print()
    else:
        user_exp = dict[item][0]

    return user_exp


# === STACK FUNCTIONS =====

def drop(stack):
    """
    Drop the last element off the stack.\n\nExample: 4 3 d --> x: 4
    """
    stack.pop(0)
    return stack


def dup(stack):
    """
    Duplicate the last stack element. <ENTER> with nothing else on the command line will also duplicate x.\n\nExamples:\n4 dup --> 4 4\n\n4 <enter> <enter> --> y: 4  x: 4 
    """
    x = stack[0]
    stack.insert(0, x)
    return stack


def get_lastx(stack, lastx_list):
    """
    Put the last x value on the stack.\n\nExamples:\n4 5 ^ --> x: 1024\nlastx --> y: 1024  x: 5\n\n3 4 lastx --> z: 3  y: 4  x: 4 (duplicates x)
    """
    stack.insert(0, lastx_list[-1])
    return stack


def list_stack(stack):
    """
    Display the contents of the entire stack.
    """
    stack_names = [' x', ' y', ' z', ' t']
    print()

    # stack must always have at least 4 elements
    while len(stack) < 4:
        stack.insert(len(stack), 0.0)
        
    # add blank stack_names, as needed
    r = '  '
    for i in range(len(stack) - 4):
        stack_names.append(r)
    
    print('='*15, ' CURRENT STACK ', '='*15)
    for register in range(len(stack)-1, -1, -1):
        # get the number of decimals from {settings}
        dp = settings['dec_point']

        if (stack[register] > 1e9 or stack[register] < (-1 * 1e8)) and (stack[register] != 0.0):
            # switch to scientific notation
            fs = ('{:.0' + dp + 'e}').format(stack[register])
        else:
            # switch to regular number notation
            fs = ('{:.0' + dp + 'f}').format(stack[register])

        # line up decimal points
        p = 11 + len(fs) - fs.find('.')

        print(stack_names[register], ':',
              ('{:>' + str(p) + '}').format(fs), sep='')

    print('='*45)

    return stack


def print_tape(stack, tape):
    """
    Print the tape (a running record of all expressions) from the current session.
    """
    tape = tape[0:-1] if tape[-1] == 'tape' else tape
    print('='*19, ' TAPE ', '='*20, sep='')
    ndx = 0
    while True:
        try:
            if tape[ndx] not in ['about', 'com', 'con', 'const', 'list', 'man', 'math', 'set', 'short', 'user', 'usercon', 'c', 'q', 'u', ]:
                print(tape[ndx])
            # , '=', tape[ndx+1])
            ndx += 1
            if ndx >= len(tape):
                break
        except IndexError:
            break
    print('='*45)
    return tape

def roll_up(stack):
    """
    Roll the stack up. x-->y, y-->z, z-->t, and t wraps around to become x.
    """
    x, y, z, t = stack[0], stack[1], stack[2], stack[3]
    stack[0], stack[1], stack[2], stack[3] = t, x, y, z

    return stack
    
    
def roll_down(stack):
    """
    Roll the stack down. t-->z, z-->y, y-->x, and x wraps around to become t.
    """
    x, y, z, t = stack[0], stack[1], stack[2], stack[3]
    stack[0], stack[1], stack[2], stack[3] = y, z, t, x
    return stack


def round_y(stack):
    """
    Round y by x.\n\nExample 3.1416 2 r --> x: 3.14
    """
    x, y = int(stack[0]), stack[1]
    if x < 0:
        print('='*45)
        print('Cannot round by a negative number.')
        print('='*45)
    else:
        stack.pop(0)
        stack[0] = round(y, x)
    return stack


def split_number(stack):
    """
    Splits x into integer and decimal parts.\n\nExample: 3.1416 split --> y: 3  x: 0.1416
    """
    n = stack[0]
    n_int = int(n)
    n_dec = n - n_int
    stack.insert(0, n_int)
    stack.insert(0, n_dec)
    return stack


def square_root(stack):
    """
    Find the square root of x.\n\nExample: 25 sqrt --> x: 5
    """
    x = stack[0]
    if x >= 0:
        stack.pop(0)
        stack.insert(0, math.sqrt(x))
    else:
        print('='*45)
        print('Square root of a negative number is undefined.')
        print('='*45)
    return stack


def stats(stack):
    """
    Summary stats for stack.\n\nResults include:\n-- Count\n-- Mean\n-- Median\n-- Standard deviation\n-- Minimum\n-- Maximum\n-- Sum\n\nNote: This function is non-destructive: the stack is left intact.
    """
    # strip out all the zero values at the beginning of a copy of [stack]
    stack_copy = stack.copy()
    for i in range(len(stack_copy)-1, 0, -1):
        if stack_copy[i] == 0:
            stack_copy.pop(i)
        else:
            break
    print()
    
    # get the stats: count, mean, median, min, max, sum; save sd for later
    cnt = len(stack_copy)
    mn = sum(stack_copy)/len(stack_copy)
    md = statistics.median(stack_copy)
    minimum = min(stack_copy)
    maximum = max(stack_copy)
    sm = sum(stack_copy)

    fs = '{:.' + settings['dec_point'] + 'f}'
    print('='*12, ' SUMMARY STATISTICS ', '='*13, sep='')
    print('        Count:', fs.format(cnt))
    print('         Mean:', fs.format(mn))
    print('       Median:', fs.format(md))

    err = '' # required if there's a statistics error
    # get standard deviation, catching potential error
    try:
        sd = statistics.stdev(stack_copy)
        print('      St. dev:', fs.format(sd))

    except statistics.StatisticsError:
        sd = ''
        err = "Standard deviation requires at least two data points,\nonly one of which can be zero."
        print('      St. dev: not computed')

    print('      Minimum:', fs.format(minimum))
    print('      Maximum:', fs.format(maximum))
    print('          Sum:', fs.format(sm))
    if err: print('\n', err, '\n', sep='')

    print('='*45)
    print("Zero values 'above' the first non-zero element in\nstack were ignored. Use <list> to inspect stack.", sep='')
    return None


def swap(stack):
    """
    Swap x and y values on the stack.\n\nExample (1): 4 3 swap --> y: 3  x: 4\n\nExample (2) 4 3 s --> y: 3  x 4\n\nNote that example (2) uses a shortcut. To list shortcuts, type: short
    """
    stack[0], stack[1] = stack[1], stack[0]
    return stack


def trim_stack(stack):
    """
    Remove all elements on the stack except the x, y, z, and t registers.\n\nNote: You can use <list> to inspect the entire stack.
    """
    stack = stack[0:4]
    print()
    return stack


# === COLOR FUNCTIONS ====

def hex_to_rgb(stack, item):
    """
    Convert hex color to rgb.\n\nExample: #b31b1b rgb --> z: 179  y: 27  x: 27\n\nNOTE: to detect a hex value, the string you enter must begin with #.
    """
    item = item[1:]
    r, g, b = int(item[0:2], 16), int(item[2:4], 16), int(item[4:6], 16)
    stack.insert(0, r)
    stack.insert(0, g)
    stack.insert(0, b)
    return stack


def rgb_to_hex(stack):
    """
    Convert rgb color (z, y, x) to hex color.\n\nExample 179 27 27 hex --> returns #b31b1b as a string.
    """
    r, g, b = hex(int(stack[2])), hex(int(stack[1])), hex(int(stack[0]))
    print('='*45)
    print('#' + str(r[2:]) + str(g[2:]) + str(b[2:]))
    print('='*45, '\n', sep='')
    return stack


def get_hex_alpha(stack):
    """
    Given a percent alpha value (between 0 and 100), return the hex equivalent, reported as a string.
    """
    n = str(int(stack[0]))
    print('='*45)
    print('alpha:', alpha[n])
    print('='*45)
    return


def list_alpha():
    """
    List alpha values and their hex equivalents.
    """
    print('\n', '='*15, ' ALPHA VALUES ', '='*16, sep='')
    for k, v in alpha.items():
        print('{:>3}'.format(k), ": ", v, sep='')
    print('='*45)
    return


# === COMMON CONVERSIONS ====

def inch(stack):
    """
    Convert cm to inches.\\Example: 2.54 inch --> x: 1 (converts 2.54 cm to 1 inch)
    """
    # 1 in = 2.54 cm
    stack[0] = stack[0] / 2.54
    return stack


def cm(stack):
    """
    Convert inches to cm.\\Example: 1.00 cm --> 2.54 (converts 1 inch to 2.54 cm)
    """
    # 1 in = 2.54 cm
    stack[0] = stack[0] * 2.54
    return stack


def lengths(stack):
    """
    Convert a decimal measurement to a fraction. For example, you can easily determine what is the equivalent measure of 2.25 inches in eighths. Very handy for woodworking.\n\nExample (1)\n2.25 8 i --> t: 2.25  z: 2  y: 2  x: 8\n\nTranslation, reading z-->x:\n2.25 inches = 2 2/8"\n\nExample (2)\n3.65 32 i --> t: 3.65  z: 3  y: 20.8  x: 32\n\nTranslation,, reading z-->x:\n3.65 inches = 3 20.8/32"\n\nExample (3)\nEnter: 3.25 then 8i\nReturns: t,z,y,z... 3.25, 3, 2, 8\n\nTranslation, reading z-->x:\n3.25" =  3 2/8"
    """
    
    # Convert a decimal measurement to 1/8", 1/16", 1/32", or 1/64"
    # Enter: X.XX >> 8, 16, 32, or 64 >> i

    if stack[0] == 0:
        print('Enter: 3.25 then 8i\nReturns: z,y,z... 3.25 3 2 8 meaning 3.25" =  3 2/8"')
    else:
        n = stack[1]
        n_int = int(stack[1])
        decimal = float(n - n_int)
        inches = stack[0]
        stack.pop(0)
        stack.insert(0, n_int)
        stack.insert(0, float(decimal * inches))
        stack.insert(0, inches)

    return stack


def ftoc(stack):
    """
    Convert temperature from F to C.\n\nExample: 212 fc --> x: 100
    """
    # e.g.: enter 32 ftco and return 0
    # C = (5/9)*(°F-32)
    result = 5 / 9 * (stack[0] - 32)
    stack.pop(0)
    stack.insert(0, round(result, 1))
    return stack


def ctof(stack):
    """
    Convert temperature from C to F.\n\nExample: 100 cf --> x 212
    """
    # e.g.: enter 0C ctof and return 32F
    # F = (9/5)*(°C)+32
    result = ((9 / 5) * stack[0]) + 32.0
    stack.pop(0)
    stack.insert(0, round(result, 1))
    return stack


def go(stack):
    """
    Convert weight from grams to ounces.
    """
    # e.g.: enter 16g and return 453.59237
    stack[0] = stack[0] * 16.0 / 453.59237
    return stack


def og(stack):
    """
    Convert weight from ounces to grams.
    """
    # e.g.: enter 16g and return 453.59237
    stack[0] = stack[0] * 453.59237 / 16.0
    return stack


# MEMORY STACK FUNCTIONS ====================

def mem_add(stack, mem):
    """
    Add x to y memory register.\n\nExample: 1 453 M+ --> adds 453 to the current value of the #1 memory register.
    """
    register, register_value = str(int(stack[1])), stack[0]

    # if the register already exists, add value to what's there
    if register in mem.keys():
        current_value = mem[register]
        # just in case register holds something other than a number
        try:
            stack.pop(0)
            stack.pop(0)
            mem.update({register: register_value + current_value})
        except:
            print('No operation conducted.')
    else:
        try:
            stack.pop(0)
            stack.pop(0)
            mem.update({register: register_value})
        except:
            print('No operation conducted.')

    return mem


def mem_sub(stack, mem):
    """
    Subtract x from y memory register.\n\nExample 1 12 M- --> Subtracts 12 from the current value of the #1 memory register.
    """
    register, register_value = str(int(stack[1])), stack[0]

    # if the register already exists, add value to what's there
    if register in mem.keys():
        current_value = mem[register]
        # just in case register holds something other than a number
        try:
            stack.pop(0)
            stack.pop(0)
            mem.update({register: register_value - current_value})
        except:
            print('No operation conducted.')
    else:
        try:
            stack.pop(0)
            stack.pop(0)
            mem.update({register: register_value})
        except:
            print('No operation conducted.')

    return mem


def mem_recall(stack, mem):
    """
    Put x register value on stack.\n\nExample: 1 MR --> puts the value of the #1 memory register on the stack.
    """
    register = str(int(stack[0]))
    # first, make sure the register exists in {mem}
    if register in mem.keys():
        stack.pop(0)
        stack.insert(0, mem[register])
    else:
        print('='*45)
        print('Memory register', str(int(stack[0])), 'does not exist.')
        print('Use <ML> to list registers.')
        print('='*45)

    return stack


def mem_list(stack, mem):
    """
    List members of memory register.
    """
    print('\n', '='*15, ' MEMORY STACK ', '='*16, sep='')
    for k, v in mem.items():
        print('Register ', k, ': ', v, sep='')
    print('='*45, sep='')


# HELP ====================

def help(stack):
    """
===================== HELP ======================
<basics>: the basics of RPN
<advanced>: how to use THIS calculator

You can also type:

h [command] 

to get information about a specific command.
"""

    txt = """
===================== HELP ======================
<basics> : the basics of RPN
<advanced> : how to use THIS calculator

You can also type:

h [command]

to get information about a specific command. Example:

h help
=================================================="""

    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack
    

def basics(stack):
    """
    The basics of RPN.\n\nType:\n\nbasics\n\nto display help on the basics of how RPN calculators work.
    """
    txt = """
================ HELP: RPN BASICS ================
An RPN calculator has no <ENTER> key. Rather, numbers are placed on a "stack" and then an operation is invoked to act on the stack values. The result of the operation is placed back on the stack.
            
EXAMPLE:
                
Type: 3 <enter>      4 <enter>
            
When 3 is entered, it goes to the x register. Then, when 4 is entered, 3 is moved to the y register and 4 is placed in the x register. Now, you can do anything you want with those two numbers. Let's add them.
            
Type: + <enter>
            
The x and y registers are added, and the result (7) appears on the stack.
        
The speed of RPN is realized when entering expressions:
            
Type: 3 4 +
            
ada parses the whole expression at once to give the same result: x: 7

You can also group items using parentheses. Example: 

(145 5+)(111 20+)- 

The result of the first group is placed on the stack in x. Then it is moved to y when the second group is placed in x. Then the minus operator subtracts x from y. This type of operation is where the real power of RPN is realized. 
=================================================="""
        
    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack


def advanced(stack):
    """
    Advanced help: how to use THIS calculator.\n\nType:\n\nadvanced\n\nfor information about advanced use of RPN and, in particular, this command-line calculator.
    """
    txt = """ 
============= ' HELP: HOW TO USE ada =============
You can get information a list of available operations by typing:

man

or by typing:

h [command]

where [command] is any command in the lists of commands, operations, and shortcuts. All of the common calculator operations are available, either as shortcuts or commands.

Numbers entered in a sequence MUST be separated by spaces, for obvious reasons. A single shortcut can follow a number directly, but sequences of shortcuts or operations using words must use spaces. For example, put the following numbers on the stack:

z: 4
y: 7
x: 3

We want to drop 3, swap 4 and 7, then get the square root of 4, to yield the result: 2.0. Expressions (1) and (2) are valid, but expressions (3) and (4) will yield an unexpected result.

(1) 4 7 3 d s sqrt
(2) 4 7 3d s sqrt
(3) 4 7 3ds sqrt
(4) 4 7 3 dssqrt

Except for functions related to the memory registers (M+, MR, etc.), commands/operators use lower case only. Not having to use the <shift> key increases speed of entry.

ada keeps track of expressions you use, and these can be displayed by typing: 

tape

The tape provides a running list of expressions entered during the current session. You can use the up and down arrow keys to cycle through items you have entered.

Besides the stack, ada provides three other features of interest. 

1. Memory register, where you can store, add, subtract, and recall numbers by accessing these registers by their number. [commands: M+, M-, MR, and ML]

2. User-defined constants, where you can store constants by name. These are saved between sessions. Put a constant's value on the stack by typing its name. [commands: const and user]

3. Conversion between RGB and hex colors, including alpha values. [commands: alpha, rgb, and hex]

There's more! Explore the manual (man) to see more of ada's capabilities.
=================================================="""

    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack


def wrap_text(txt):
    """
    Print text wrapped by TextWrapper.
    """
    wrapper = textwrap.TextWrapper(width=50)
    explanation = wrapper.wrap(text=txt)
    for line in explanation:
        print(line)
    return


def fold(txt):
    """
    Textwraps 'txt'; used only by help_fxn.
    """
    return textwrap.fill(txt, width=50)


def help_fxn(stack, item):
    """
    Help for a single command.\n\nExample: h sqrt --> Find the square root of x.
    """

    # get a list of all functions and their docStrings
    func, docString = {}, ''
    for i in getmembers(modules[__name__], predicate=lambda f: isfunction(f) and f.__module__ == __name__):
        func.update({i[0]: i[1].__doc__.strip('\n').strip()})

    if item in op1.keys():
        f = op1[item]
    elif item in op2.keys():
        f = op2[item]
    elif item in commands.keys():
        f = commands[item]
    elif item in constants.keys():
        f = constants[item]
    elif item in shortcuts.keys():
        f = shortcuts[item]
    else:
        print('Help not found.')

    # Now that you have the function name, go back to func and get the docString
    print('='*45)
    print(item)
    txt = func[f[0].__name__]
    print('\n'.join([fold(txt) for txt in txt.splitlines()]))
    print('='*45)
    
    return


# __main__: GLOBAL FUNCTIONS AND RUN RPN() ====================

if __name__ == '__main__':

    print('ada - an RPN calculator v2.3')

    # initialize the x, y, z, and t registers, as well as the entered_value variable
    stack, entered_value = [0.0], 0.0
    lastx_list, mem, tape = [0.0], {}, []
    letters = ascii_letters + '_' + ':'
    lower_letters = ascii_lowercase + '_' + ':'
    user_exp = ''

    # default settings:
    # number of decimal places = 4
    settings = {
                'dec_point': '4',
                'delimiter': ',',
                'show_tape': 'N'
                }

    # menu gets printed on screen 4 items to a line
    menu=( 
        '<d>rop       ', '<s>wap       ', '<r>oll <u>p  ', '<r>oll<d>own',
        '<n>eg        ', '<c>lear      ', '<usercon>stants', '',
        '<set>tings   ', '<man>ual     ', '<h> [...]    ', '<q>uit       '
        )
    # operations that modify or use x only (stack[0])
    # these are functions that take only a float (not the [stack])
    op1 = {
        "log": (log, "log10(x)"),
        "ceil": (ceil, "6.3->7"),
        "floor": (floor, "6.9->6"),
        "!": (factorial, "x factorial"),
        "abs": (absolute, "absolute value of x"),
        "n": (negate, "negative of x"),
        "sin": (sin, "sin(x) -- x must be radians"),
        "cos": (cos, "cos(x) -- x must be radians"),
        "tan": (tan, "tan(x) -- x must be radians"),
        "asin": (asin, "asin(x) -- x must be radians"),
        "acos": (acos, "acos(x) -- x must be radians"),
        "atan": (atan, "atan(x) -- x must be radians"),
        "pi": (pi, "pi"),
        "sqrt": (square_root, "sqrt(x)"),
        "deg": (deg, "convert angle x in radians to degrees"),
        "rad": (rad, "convert angle x in degrees to radians"),
        "rand": (random_number, 'random int between x and y.'),
        "    ": ('', ''),
        "====": ('', '==== CONVERSIONS ===='),
        'bin': (convert_to_binary, 'Convert x to binary'),
        "dec": (convert_to_decimal, 'Convert x from binary to decimal.'),
        'cm': (cm, 'Convert inches to centimeters.'),
        'inch': (inch, 'Convert centimeters to inches.'),
        'cf': (ctof, 'Convert centigrade to Fahrenheit.'),
        'fc': (ftoc, 'Convert Fahrenheit to centigrade.'),
        'go': (go, 'Convert weight from grams to ounces.'),
        'og': (og, 'Convert weight from ounces to grams.'),
        'i': (lengths, 'Convert decimal measure to fraction.'),
    }

    # operations that require both x and y (stack[0] and stack[1])
    # these are functions that take two floats (not the [stack])
    op2 = {
        "    ": ('', ''),
        "====": ('', '==== STANDARD OPERATORS ===='),
        "+": (add, "y + x"),
        "-": (sub, "y - x"),
        "*": (mul, "y * x"),
        "x": (mul, "y * x"),
        "/": (truediv, "y / x"),
        "%": (mod, "remainder from division"),
        "^": (pow, "y ** x"),
    }

    # commands that use functions to manipulate the stack or its contents
    # these are functions that take the entire [stack] (and may or may not use it)
    commands = {
        "about": (about, "Information about the author and product."),
        'set': (calculator_settings, 'Access and edit settings.'),
        "     ": ('', ''),
        " ====": ('', '==== COLOR ===='),
        'alpha': (get_hex_alpha, 'Hex equivalent of RGB alpha value.'),
        'hex': (rgb_to_hex, 'Convert rgb color (z, y, x) to hex color.'),
        "list_alpha": (list_alpha, "List all alpha values."),
        'rgb': (hex_to_rgb, 'Convert hex color to rgb.'),
        "      ": ('', ''),
        "  ====": ('', '==== HELP ===='),
        "man": (manual, "Menu to access parts of the manual."),
        "com": (print_commands, "All commands and math operations."),
        "con": (print_constants, 'List constants and conversions.'),
        'help': (help, 'Getting help.'),
        "basics": (basics, "The basics of RPN."),
        "advanced": (advanced, 'Advanced help: how to use THIS calculator.'),
        "short": (print_shortcuts, 'Available shortcut functions.'),
        "       ": ('', ''),
        "   ====": ('', '==== MEMORY REGISTERS ===='),
        "M+": (mem_add, 'Add x to y memory register.'),
        "M-": (mem_sub, 'Subtract x from y memory register.'),
        "MR": (mem_recall, 'Put x register value on stack.'),
        "ML": (mem_list, 'List elements of memory register.'),
        "        ": ('', ''),
        "    ====": ('', '==== STACK MANIPULATION ===='),
        "clear": (clear, "Clear all elements from the stack."),
        "drop": (drop, "Drop the last element off the stack."),
        "dup": (dup, "Duplicate the last stack element."),
        "lastx": (get_lastx, "Put the lastx value on the stack."),
        "list": (list_stack, "Show the entire stack."),
        "rolldown": (roll_down, "Roll stack down."),
        "rollup": (roll_up, "Roll stack up."),
        "split": (split_number, "Splits x into integer and decimal parts."),
        'stats': (stats, 'Summary stats for stack (non-destructive).'),
        "swap": (swap, "Swap x and y values on the stack."),
        'tape': (print_tape, "Print the tape from the current session."),
        "trim": (trim_stack, 'Remove stack, except the x, y, z, and t.'),
        "math": (print_math_ops, "Print math operations."),
        "         ": ('', ''),
        "     ====": ('', '==== USER-DEFINED ===='),
        "usercon": (print_dict, "List user-defined constants, if they exist."),
        "user": (define_constant, 'Add/edit user-defined constant; save to file.'),
        "user_exp": (get_user_expression, 'Retrieve a user-defined expression from file.'),
    }

    # http://www.onlineconversion.com
    # constant names MUST be lowercase
    constants = {
        "avogadro": (6.022_140_9e+23, "avogadro's number"),
        "golden_ratio": (1.618033988749895, 'golden ratio'),
        "gram": (0.035_273_961_95, "ounce"),
        "inches_hg": (25.399_999_705, "mmHg"),
        "kilogram": (2.204_622_621_8, "pound"),
        "kilometer": (0.621_371_192_24, 'mile'), 
        "light":  (299_792_458, "speed of light, m/s"),
        "mmhg": (0.535_240_171_45, "inches of water"),
        "parsec": (19_173_510_995_000, 'mile'),
    }

    shortcuts = {
            'c': (clear, 'Clear all elements from the stack.'),
            'd': (drop, 'Drop the last element off the stack.'),
            'ue': (get_user_expression, "Get user expression from file."),
            'h': (help, 'Help for a single command.'),
            'n': (negate, 'Negative of x.'),  
            'q': ('', 'Quit.'),
            'r': (round_y, 'round y by x'),
            'rd': (roll_down, 'Roll the stack down.'),  
            'ru': (roll_up, 'Roll the stack up.'),  
            's': (swap, 'Swap x and y values on the stack.'),
            }

    # keys are "percent transparency" and values are "alpha code" for hex colors
    # 0% is transparent; 100% is no transparency
    alpha = {
            '100': 'FF',  
            '95': 'F2',  
            '90': 'E6',  
            '85': 'D9',  
            '80': 'CC',  
            '75': 'BF',  
            '70': 'B3',  
            '65': 'A6',  
            '60': '99',  
            '55': '8C',
            '50': '80',  
            '45': '73',  
            '40': '66',  
            '35': '59',  
            '30': '4D',  
            '25': '40',  
            '20': '33',  
            '15': '26',  
            '10': '1A',  
            '5': '0D',  
            '0': '00'
            }


    # when calculator starts, read constants.json if it exists
    # this way, the user has access to user-defined constants without
    # having to do anything special
    try:
        with open("constants.json") as file:
            dict = json.load(file)
    except FileNotFoundError:
        dict = {}

    RPN(stack, dict, lastx_list, mem, settings, tape, user_exp)
