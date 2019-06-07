"""
ada.py
Richard E. Rawson

Command line RPN calculator that performs a variety of common functions.

"""

# version_num is in "if __name__ == '__main__':" 
    # ? -- versioning: x.y z
    # ?    Where:
    # ?        x = main version number
    # ?        y = feature number, 0-9. Increase this number if the change contains new features with or without bug fixes.
    # ?        z = revision datetime

# ! Best info on GIT branching strategy:
    # ? https://nvie.com/posts/a-successful-git-branching-model/
"""
MANAGING A MERGE TO DEVELOP:
$ git checkout develop
$ git merge --no-ff features
$ git push origin develop
"""

# todo -- the .exe file created by pyinstaller does not read files; it creates config.json and constants.json, but doesn't read them after creating them

import json
import math
import operator
import random
import statistics
import textwrap
from inspect import getmembers, isfunction
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from sys import modules


# MAIN CALCULATOR FUNCTION ====================

def RPN(stack, user_dict, lastx_list, mem, settings, tape):
    """
    Main function that gets user's input and does initial processing. This means that some inputs can be handled easily, but most will require further processing by process_item() which will return a [list] of individual items that the user entered.
    """

    while True:
        quit = False
        
        # print the tape if requested in {settings}
        if settings['show_tape'] == 'Y':
            print_tape(stack, tape)

        # print the register
        stack = print_register(stack, settings)

        # generate the menu
        if settings['show_menu'] == 'Y':
            print()
            for i in range(0, len(menu), 4):
                m = ''.join(menu[i:i+4])
                print(m)

        # print user tip, optionally
        if settings['show_tips'] == 'Y':
            print('\nType:\n     basics\nto get started with RPN.')
            # only show tip once
            settings['show_tips'] = 'N'

        # get the command line entry from the user
        entered_value = input('\n').lstrip().rstrip()
        
        # make sure parentheses are balanced before proceeding
        lst = list(entered_value)
        if lst.count('(') - lst.count(')') != 0:
            print('Unbalanced parentheses.')
            continue

        # add the current expression to the tape
        tape.append(entered_value)

        # if <ENTER> alone was pressed, duplicate the x: value on the stack and then <continue>
        if len(entered_value) == 0:
            x = stack[0]
            stack.insert(0, x)
            continue

        # ==========================================================
        # HERE, WE START INITIAL PROCESSING OF entered_value
        # ==========================================================

        # if item is the name of a user-defined constant...
        if entered_value in user_dict.keys():
            # get the user-defined constant/expression, itself
            entered_value = str(user_dict[entered_value][0])

        # if the entered_value begins with a '#', then it's a hex number, requiring special handling
        if entered_value[0] == '#':
            # then this is a hex number to be converted to rgb
            stack = hex_to_rgb(stack, entered_value)
        
         # if entered_value is a hexadecimal value, beginning with '0x'
        elif entered_value[0:2] == '0x':
            stack = convert_hex_to_dec(stack, entered_value.split(' ')[0][2:])
            continue

        # if entered_value is a binary number beginning with "0b"
        elif entered_value[0:2] == '0b':
            stack = convert_bin_to_dec(stack, entered_value.split(' ')[0][2:])
            continue
        
        # otherwise, we're going to have to parse what the user entered
        else:
            # put each "item" in user's entry into a [list]
            stack, entered_list = parse_entry(stack, entered_value)

            # process each item (number, operator, shortcuts, commands, etc.) in [entered_list]
            ndx = 0
            while ndx < len(entered_list):

                item = entered_list[ndx]

                # process shortcuts
                # 'q' (quit) is special because it does not have a fxn
                if item in shortcuts.keys():
                    if item == 'q':
                        quit = True
                    elif item == 'h':
                        try:
                            # h q will cause calculator to quit
                            if entered_list[ndx+1] != 'q':
                                help_fxn(stack, entered_list[ndx+1])
                                ndx += 1
                            else:
                                print('='*45)
                                print('q\nQuit calculator.')
                                print('='*45)
                                entered_list[ndx+1] = ''
                                ndx += 1
                        except:
                            # h by itself:
                            print('='*45)
                            print('For help with individual commands, type:')
                            print('\nh [command]\n', sep='')
                            print('where [command] is any command or operation.\n\nType:\n\nindex\n\nto access lists of commands and operations.', sep='')
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
                        stack, lastx_list, tape, user_dict = process_item(
                            stack, user_dict, lastx_list, mem, settings, tape, item)
                    ndx += 1
                    continue
                
                # if '(', then this is the start of a group; a result is obtained for each group
                elif item == '(':
                    while item != ')':
                        stack, lastx_list, tape, user_dict = process_item(
                            stack, user_dict, lastx_list, mem, settings, tape, item)
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
            # save {settings} to disk before quitting
            with open('config.json', 'w+') as file:
                file.write(json.dumps(settings, ensure_ascii=False))
            print('\nEnd program.\n')
            return None

    return stack

# EXPRESSION EVALUATION FUNCTIONS ====================

def process_item(stack, user_dict, lastx_list, mem, settings, tape, item):
    """
    Process an item from [entered_list]. Return a modified [stack] (or modified {settings}).

    Takes an item in entered_list, which is going to be anything except a shortcut, and figures out what to do with it.
    """

    # if it's a '(' or ')', we have the start or end of a group; do nothing
    if item in ['(', ')']:
        pass

    # if item is a float
    elif type(item) == float:
        stack.insert(0, item)
        # save this item as lastx
        lastx_list = [lastx_list[-1]]
        lastx_list.append(stack[0])

    # if item is a math operator only requiring x:
    elif item in op1:
        stack = math_op1(stack, item)

    # if item is a math operator requiring both x: and y:
    elif item in op2:
        stack = math_op2(stack, item)

    # if operator is in {commands}, {shortcuts}, or {constants}
    elif item in commands or item in shortcuts or item in constants:

        # default code that runs:
        #      operation(stack)
        #      stack = operation(stack)
        if item in commands:
            operation = commands[item][0]
        elif item in shortcuts:
            operation = shortcuts[item][0]
        elif item in constants:
            stack.insert(0, constants[item][0])

        # following are items that have to be handled differently
        if item == 'lastx':
            stack = operation(stack, lastx_list)
        elif item == 'user':
            stack, user_dict = define_constant(stack, user_dict)
        elif item in ['M+', 'M-', 'MD', 'MR', 'ML']:
            mem = operation(stack, mem)
        elif item == 'set':
            settings = operation(settings)
            return settings
        elif item == 'tape':
            tape = print_tape(stack, tape)
        else:
            if item not in constants:
                stack = operation(stack)

    # any unrecognized operation (a garbage entry)
    # is ignored, the user is notified, and the program simply continues...
    else:
        print('='*45)
        print('Unknown command.')
        print('='*45)

    return stack, lastx_list, tape, user_dict


def parse_entry(stack, entered_value):
    """
    From the user's entered value, parse out each valid element. Put each distinct element (character/operator/number) of the user's entered_value into a list.

    Example: Each of the following characters, delimited by spaces, is a single element that will be added to [entered_list]: 
    
    '( 43 62 s d dup + )' --> ['(', '43', '62', 's', 'd', 'dup', '+, ')']

    This fxn has the challenge of figuring out exactly WHAT string of characters qualifies as a single item. For example, in the above expresson, "d" as a lone character is one item while the 'd' in 'dup' belongs with 'up' to form "dup" as one item. 
    
    Return entered_list to RPN().
    """

    data, j, entered_list, s = [], 0, [], ''

    # if the entered values is not a key in {op1} or {op2}...
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

            # if it's a alphabetic character, gather all the following characters into one string
            elif entered_value[ndx] in letters:
                while entered_value[ndx] in letters:
                    s += entered_value[ndx]
                    try:
                        if entered_value[ndx+1] in lower_letters:
                            ndx += 1
                        elif entered_value[ndx] == 'M' and entered_value[ndx+1] in ['+', '-', 'D', 'L', 'R']:
                            s += entered_value[ndx+1]
                            ndx += 1
                            break
                        else:
                            break
                    except IndexError:
                        break

            # if it's a single-character math operator (all of {op2] 
            # and only '!' in {op1})
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

    # in case x:, y:, z:, t: are used, the values in those registers now reside in entered_value, so delete them from the stack
    for ndx, r in enumerate(['x:', 'y:', 'z:', 't:']):
        if r in entered_value:
            stack[ndx] = 0.0
    
    # convert numbers to floats and strip out empty elements  and punctuation(e.g., commas, as in, comma delimited number sequences)
    for i in data:
        if i in [',', ';', ':']:
            i = ' '
        if i.rstrip() or i in ['(', ')']:
            try:
                entered_list.append(float(i))
            except:
                entered_list.append(i)

    return stack, entered_list


def print_register(stack, settings):
    """
    Display the stack register.
    """

    stack_names = [' x', ' y', ' z', ' t']
    print()

    # stack must always have at least 4 elements
    while len(stack) < 4:
        stack.insert(len(stack), 0.0)

    # make sure the stack contains only numbers
    stk = list(reversed(stack))
    for ndx, i in enumerate(stk):
        try:
            r = int(i)
        except ValueError:
            stk.pop(ndx)
    stack = list(reversed(stk))

    # format and print the four registers
    for register in range(3, -1, -1):
        # get the number of decimals and the thousands separator from {settings}
        dp = settings['dec_point']
        separator = settings['separator']

        # set the formatting of the numbers
        if (stack[register] > 1e7 or
                stack[register] < -1 * 1e6) and (stack[register] != 0.0):
            # switch to scientific notation
            fs = ('{:'+ separator + '.0' + dp + 'e}').format(stack[register])
        else:
            # switch to regular number notation
            fs = ('{:' + separator + '.0' + dp + 'f}').format(stack[register])

        # line up decimal points
        p = 11 + len(fs) - fs.find('.')

        # print the register
        print(stack_names[register], ':',
              ('{:>' + str(p) + '}').format(fs), sep='')

    return stack

#  IMPORT FILE FUNCTIONS ====================

def get_file_data(stack):
    """
    Import a text file and put the data on the stack.
    
Since the stack is only a list of numbers, the file that you import should contain only one column of numbers. Lines that don't contain numbers will be skipped.
    """
    data_file = input('File name: ')

    # read the data file
    try:
        with open(data_file, 'r') as f:
            file = f.readlines()

    # notify user if no file was found
    except FileNotFoundError:
        print('='*45)
        print('File not found. Stack unmodified.')
        print('='*45)
        return stack

    # read the values into the stack; skip any line that is not a number
    stack, cnt = [], 0
    for line in file:
        try:
            stack.append(float(line.strip('\n')))
            cnt += 1
        except ValueError:
            pass
    
    # provide a report to the user
    print('='*18, ' REPORT ', '='*19, sep='')
    print('   Lines in file:', len(file))
    print('Numbers imported:', cnt)
    print('='*45, sep='')

    return stack

 
# PRINT FUNCTIONS (INDEX) ====================

def manual(stack):
    """
    Menu to access the various parts of the index.
    """
    txt, line_width = ' INDEX ', 45
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
    return stack


def print_commands(stack):
    """
    List all available commands, including those that manipulate the stack. To get a list of math operators, shortcuts, or constants, type:

    math --> (math operators)

    short --> (shortcuts)

    con --> (built-in constants)
    """
    # print all the keys in {shortcuts}
    txt, line_width = ' COMMANDS ', 56
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in commands.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')

    return stack


def print_math_ops(stack):
    """
    List all math operations. to get a list of commands, shortcuts, or constants, type:

    com --> (commandsd)

    short --> (shortcuts)

    con --> (built-in constants)
    """
    # print all the keys, values in {op1} and {op2}
    txt, line_width = ' MATH OPERATIONS ', 56
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in op1.items():
        print('{:>13}'.format(k), '|', v[1])

    for k, v in op2.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')

    return stack


def print_shortcuts(stack):
    """
    List shortcuts to math functions. To get a list of commands, math operations, or constants, type:

    com --> (commands)

    math --> (math operators)

    con --> (built-in constants)
    """
    # print all the keys, values in {shortcuts}
    txt, line_width = ' SHORTCUTS ', 56
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in shortcuts.items():
        print('{:>13}'.format(k), '|', v[1])

    print('='*line_width, sep='')
    return stack


def print_constants(stack):
    """
    List constants and conversions.

Note: This list does not include user-defined constants. That list is accessed by typing:

    usercon
    """
    # print all the keys, values in {constants}
    txt, line_width = ' CONSTANTS & CONVERSIONS ', 56
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in constants.items():
        print('{:>13}'.format(k), '|', v[0], ": ", v[1], sep='')

    print('='*line_width, sep='')
    return stack


def print_dict(stack):
    """
    List user-defined constants and expressions. 
    
(1) To use a user-define constant or expression, type its name. Either the constant's value will be placed on the stack or the expression will be executed.

Related commands:
    
    usercon --> to list the current user-defined constants. 

    user --> to create user-defined (named) constants and expressions
    """
    # print all the keys, values in {user_dict}
    try:
        with open("constants.json", 'r') as file:
            user_dict = json.load(file)
    except FileNotFoundError:
        user_dict = {}

    txt, line_width = ' USER-DEFINED CONSTANTS ', 56
    ctr1 = math.floor((line_width - len(txt)) / 2)
    ctr2 = math.ceil((line_width - len(txt)) / 2)
    print('='*ctr1, txt, '='*ctr2, sep='')

    for k, v in user_dict.items():
        print(k, ': ', v[0], ' ', v[1], sep='')

    print('='*line_width, sep='')
    return stack


def print_all_functions(stack, user_dict):
    """
    All commands and math operations. 
    
    This function is not used, except by the developer.
    """

    # strategy: only get docstrings from things NOT in this list; this will be all the fxns that the user can use
    module_functions = ['RPN', 'process_item', 'parse_entry','print_register', 'calculator_settings', 'print_all_functions', 'print_commands', 'help', 'help_1', 'help_2', 'math_op1', 'math_op2', 'fold']

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
    Access and edit calculator settings. You can:

(1) change the number of decimals that display in the stack. Example: 8p will change stack to show 8 decimal places.

(2) turn the thousands separator on or off.

(3) display the tape, updated after each expression is evaluated.
    """
    # retrieve settings from config.json
    try:
        with open("config.json", 'r') as file:
            settings = json.load(file)
    except FileNotFoundError:
        # save default settings to config.json:
        settings = {
                'show_menu': 'Y',
                'dec_point': '4',
                'separator': ',',
                'show_tape': 'N',
                'show_tips': 'Y',
                }
        with open('config.json', 'w+') as file:
            file.write(json.dumps(settings, ensure_ascii=False))

    while True:
        # print the current settings
        print('\n', '='*13, ' CURRENT SETTINGS ', '='*13, sep='')
        for k, v in settings.items():
            if k == 'show_menu':
                print('     Show menu:', v)
            elif k == "dec_point":
                print('Decimal points:', v)
            elif k == 'separator':
                if settings['separator'] == '':
                    print('     Separator: ', 'none', sep='')
                else:
                    print('     Separator: ', ',', sep='')
            elif k == 'show_tape':
                print('     Show tape: ', v)
            # elif k == 'show_tips':
            #     print('  Restart tips: ', v)
            else:
                pass
        print('='*45)

        # print a menu of setting options
        s = input(
            "\n          Display <m>enu\
            \n      Set decimal <p>oint \
            \nSet thousands <s>eparator \
            \n              Show <t>ape \
            \n                   <E>xit\n").lower()
        if not s:
            break

        # change menu setting
        if s[0].strip().lower() == 'm':
            m = input('Calculator menu (ON/OFF) ')
            if m.strip().upper() == 'OFF':
                settings['show_menu'] = 'N'
            else:
                settings['show_menu'] = 'Y'

        # change decimal point setting
        elif s[0].strip().lower() == 'p':
            # usage example: enter <p8> or <p 8> to set decimal points to 8 places
            # enter <p> to generate step-by-step process
            # entering <map> or <pee> generates usage help

            if not (s[1:].strip()): # user entered only <p>
                 while True:
                    s = input("Enter number of decimal points: ")
                    try:
                        t = int(s) # if this fails, user did not enter int
                        settings['dec_point'] = str(int(s))
                        break
                    except:
                        print('Enter only an integer.')
                        continue
            # user entered <p> + a number
            else:  
                try:
                    settings['dec_point'] = str(int(s[1:])).strip()
                except:
                    print('Usage: p[number decimal points]')

        # user entered number + <p>
        elif s[-1].strip().lower() == 'p':
            try:
                settings['dec_point'] = str(int(s[:-1])).strip()
            except:
                print('Usage: p[number decimal points]')

        # change thousands separator setting
        elif s.strip() == 's':
            separator = input("Thousands separator ('none' or ','): ")
            if separator.strip().lower() == 'none':
                settings['separator'] = ''
            else:
                settings['separator'] = ','
        
        # change whether or not tape displays
        elif s.strip() == 't':
            tape = input('Show tape persistently? (ON/OFF): ') 
            if tape.strip().upper() == 'ON':
                settings['show_tape'] = 'Y'
            else:
                settings['show_tape'] = 'N'

        # change whether or not to restart user tips
        # elif s.strip() == 'tips':
        #     tips = input('Restart user tips? (Y/N) ')
        #     if tips.strip().upper() == 'Y':
        #         settings['show_tips'] = 'Y'
        #     else:
        #         settings['show_tips'] = 'N'
        else:
            pass

        # print the new settings
        print('\n', '='*15, ' NEW SETTINGS ', '='*15, sep='')
        for k, v in settings.items():
            if k == 'show_menu':
                print('     Show menu:', v)
            elif k == "dec_point":
                print('Decimal points:', v)
            elif k == 'separator':
                if settings['separator'] == '':
                    print('     Separator: ', 'none', sep='')
                else:
                    print('     Separator: ', ',', sep='')
            elif k == 'show_tape':
                print('     Show tape: ', v)
            # elif k == 'show_tips':
            #     print('  Restart tips: ', v) 
            else:
                pass
        print('='*45)

        # e or exit to exit out of settings
        if s.lower() == 'e' or s.lower() == 'exit' or not s:
            break
            
    # save {settings} to file, whether changed or not
    with open('config.json', 'w+') as file:
        file.write(json.dumps(settings, ensure_ascii=False))

    return settings


# CALCULATOR FUNCTIONS ====================

def about(stack):
    """
    Information about the author and product.
    """
    print('='*45)
    
    txt1 = 'ada - an RPN calculator\n'+ 'version: ' + version_num[0:18] + '\n' + \
          ' python: 3.7\n' + '   date: 2019-05-27\n\n'

    txt2 = 'ada is named after Ada Lovelace (1815–1852), whose achievements included developing an algorithm showing how to calculate a sequence of numbers, forming the basis for the design of the modern computer. It was the first algorithm created expressly for a machine to perform.'

    print('\n'.join([fold(txt1) for txt1 in txt1.splitlines()]))
    print('\n'.join([fold(txt2) for txt2 in txt2.splitlines()]))

    print('='*45)
    return stack


def version(stack):
    """
    Report the version number as a string.
    """
    print('='*45)
    print(version_num[0:18])
    print('='*45)
    return stack


def clear(stack):
    """
    Clear all elements from the stack.

To be distinguished from:

    trim

that removes all but the x:, y:, z:, and t: registers. 
    """
    stack, entry_value = [0.0, 0.0, 0.0, 0.0], ''
    return stack

# === MATH OPERATORS =====

def log(stack):
    """
    Returns the log(10) of the x: value.
    
Example:
    100 log --> x: 2, since 10^2 = 100.
    """
    if stack[0] <= 0:
        print('='*45)
        print('Cannot return log of numbers <= 0.')
        print('='*45)
        return stack
    x = stack[0]
    stack[0] = math.log10(x)
    return stack


def ceil(stack):
    """
    Returns to ceiling, the next higher integer, of x:
    
Example: 6.3->7
    """
    x = stack[0]
    stack[0] = math.ceil(x)
    return stack


def floor(stack):
    """
    Returns the floor, the next lower integer, of x:
    
Example: 6.9->6
    """
    x = stack[0]
    stack[0] = math.floor(x)
    return stack


def factorial(stack):
    """
    x: factorial
    
Example (1):
    4 factorial --> x: 24
    
Example (2)
    4 ! --> x: 24
    
Note that example (2) uses a shortcut. To list shortcuts, type: 

    short
    """
    if stack[0] < 0:
        print('='*45)
        print('Factorial not defined for negative numbers.')
        print('='*45)
        return stack
    x = stack[0]
    stack[0] = math.factorial(x)
    return stack


def negate(stack):
    """
    Negative of x:

Example:
    4 n --> x: -4
    """
    x = stack[0]
    stack[0] = operator.neg(x)
    return stack


def sin(stack):
    """
    sin(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.sin(x)
    return stack


def cos(stack):
    """
    cos(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.cos(x)
    return stack


def tan(stack):
    """
    tan(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.tan(x)
    return stack


def asin(stack):
    """
    asin(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.asin(x)
    return stack


def acos(stack):
    """
    acos(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.acos(x)
    return stack


def atan(stack):
    """
    atan(x) -- x: must be radians.
    """
    x = stack[0]
    stack[0] = math.atan(x)
    return stack


def pi(stack):
    """
    Puts the value of pi on the stack.
    """
    stack.insert(0, math.pi)
    return stack


def deg(stack):
    """
    Convert x: value from radians to degrees.
    """
    stack[0] = math.degrees(stack[0])
    return stack


def rad(stack):
    """
    Convert x: value from degrees to radians.
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
    Generate a random integer between y (exclusive) and x (inclusive).
    
Example:
    1 100 rand --> x: 43 (random number between 1 (exclusive) and 100 (inclusive))
    """
    # make sure x: and y: are in correct order
    x, y = int(stack[0]), int(stack[1])
    if x == y:
        print('='*45)
        print("Must have a range of numbers.")
        print('='*45)
        return stack
    if y > x:
        x, y = y, x
    ri = random.randint(y, x)
    stack.insert(0, ri)
    return stack


def add(stack):
    """
    y + x
    
Example:
    4 3 + --> x: 7
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, x + y)
    return stack   


def sub(stack):
    """
    y - x

Example:
    4 3 - --> x: 1
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y - x)
    return stack


def mul(stack):
    """
    y * x
    
Example:
    5 3 * --> x: 15
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y * x)
    return stack   


def truediv(stack):
    """
    y / x
    
Example:
    12 3 / --> x: 4
        
Note: division by zero will generate an error.
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y / x)
    return stack


def mod(stack):
    """
    Modulus: remainder from division.\n\nExample (1): 5 2 % --> x: 1
        
Example (2):
    4 2 % --> x: 0

Note: A useful fact is that only even numbers will result in a modulus of zero.
    """
    x, y = stack[0], stack[1]
    stack.pop(0)
    stack.pop(0)
    stack.insert(0, y % x)
    return stack


def pow(stack):
    """
    y to the power of x
    
Example:
    10 2 ^ --> x: 100
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

def convert_bin_to_dec(stack, bin_value):
    """
    Convert x: from binary to decimal. Replaces binary value in x: with the decimal value.
    
Example:
    0b1000 dec --> x: 8
    """
    if stack[0] < 0:
        print('='*45)
        print('Cannot find binary equivalent of a negative number.')
        print('='*45)
        return stack
    stack[0] = int(bin_value, 2)
    return stack


def convert_dec_to_bin(stack):
    """
    Convert x: from decimal to binary. Binary value is a sting so it is reported as a string, and not placed on the stack.
    
Example:
    8 bin --> "0b1000"
    
Note: the x: value remains on the stack.
    """
    print('='*45)
    print(bin(int(stack[0])))
    print('='*45)
    return stack


def convert_dec_to_hex(stack):
    """
    Convert x: from decimal to hexadecimal. Hexadecimal number is a string, so it is reported as a string, and not placed on the stack.
    """
    # SOURCE:
    # https://owlcation.com/stem/Convert-Hex-to-Decimal
    hex_dict = {
            '0':'0', '1':'1', '2':'2', '3':'3', '4':'4', '5':'5',
            '6':'6', '7':'7', '8':'8', '9':'9', '10':'A',
            '11':'B', '12':'C', '13':'D', '14':'E', '15':'F'
            }
    result = 1
    hex_value = ''
    cnt = 0
    while True:
        stack[0] = stack[0] / 16
        stack = split_number(stack)
        result = int(stack[0] * 16)
        if stack[0] == 0 and stack[1] == 0: 
            break
        result = hex_dict[str(result)]
        hex_value += result
        stack.pop(0)
        cnt += 1
    
    # a decimal value of zero, won't be caught by the while loop, so...
    if cnt == 0:
        hex_value = '0'
    hex_value = '0x' + hex_value[::-1]

    print('='*45)
    print(hex_value)
    print('='*45)

    return stack


def convert_hex_to_dec(stack, hex_value):
    """
    Convert a hexadecimal (string beginning with "0x") to decimal. Since the hexadecimal number is a string, it is not placed on the stack.
    """
    # ! RPN() handles this directly without going to process_item()
    # ! entering '0x' is sufficient to convert hex to decimal
    # ! so entering 'hexdec' actually does nothing
    # SOURCE:
    # https://owlcation.com/stem/Convert-Hex-to-Decimal
    hex_dict = {
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5',
        '6': '6', '7': '7', '8': '8', '9': '9', '10': 'A',
        '11': 'B', '12': 'C', '13': 'D', '14': 'E', '15': 'F'
    }
    hex_value = hex_value[::-1].upper()
    result = 0
    for ndx, i in enumerate(hex_value):
        n = [k for k, v in hex_dict.items() if v == i]
        result += (int(n[0]) * math.pow(16, ndx))
    stack.insert(0, result)

    return stack

# === USER-DEFINED CONSTANTS FUNCTIONS ====


def define_constant(stack, user_dict):
    """
    Define, edit, or delete a user-defined constant or expression. Once defined, constants/expressions are saved to file and retrieved automatically when the calculator starts. Names must be lower case and cannot contain spaces. You cannot redefine system names (e.g., "swap"). Two types of constants can be saved:

(1) Numerical constants. These are numbers.

    Example: 
        meaning_of_life:  42.0  a meaningful constant

(2) Expressions. These are strings.

    Example (1):
        (150 140 -) 2 / 140 + 

    Example (2):
        (y: x: - ) 2 / 140 +

The latter example show use of register names in an expression. Here is how to construct these types of expression. Let's create this expression:

    (x: y: +) y: *
    
NOTE: Keep in mind that during evaluation of the expression, the stack contents change as operations are executed. We'll see this happen in this example...

-- Let's put the following values on the stack.

    z:          7.0000
    y:          3.0000
    x:          1.0000

-- When the expression is run, the + operator adds x: and y:. y: is removed and x: is replaced with the result: 4. z: drops down to the y: register:

    z:          0.0000
    y:          7.0000
    x:          4.0000

-- Then the current x: and y: are multiplied and the result, 28, is put in the x: register:

    z:          0.0000
    y:          0.0000
    x:         28.0000

NOTES: 
(1) The non-obvious point is that, in an expression, the registers (e.g., "x:") are not variable names, but refer to the stack at THAT point in the expression's execution.

(2) Simple use of register names can save a lot of time when repeating simple calculations, such as getting the mid-point between two values. Create and save the following expression, say as "mid". 

    y: x: s dup rd - 2 / s d +

Put any two values on the stack, and run the expression by typing:

    mid

An easy way to get the expression: use the command line to do what you need, then copy the steps from the tape. Format into one line, if needed, and then paste in the VALUE field when you create the user-defined expression using:

    user

(3) User-define constant/expression names cannot be used as part of a sequence. For example:

    100 50 mid  -- invalid

    100 50      -- put values on stack first
    mid         -- valid

(4) Memory registers can act as variables, and may be better suited for some complicated expressions. See help for M+, M-, MR, and ML.
    
Type:
    
    usercon

to list the current user-defined constants. 
    """
    try:
        with open("constants.json", 'r') as file:
            user_dict = json.load(file)
    except:
        user_dict = {}

    while True:
        name, value, description = '', '', ''
        print('\n', '='*10, ' USER-DEFINED CONSTANTS ', '='*11, sep='')
        for k, v in user_dict.items():
            print(k, ': ', v[0], ' ', v[1], sep='')
        print('='*45)

        while True:
            print()
            print('NAME: lowercase; avoid names already in use.')
            print('VALUE: Enter either a number or an expression.')
            print('   If you need information on expressions,\n   press <enter> then:\n\nh user\n')
            print()
            name = input("Name of constant/conversion: ")
            
            # if no name was entered, leave this function
            if not name:
                break

            # check to see if there are any uppercase letters: ada can't handle them.
            upper = False
            for i in range(len(name)):
                if name[i] in ascii_uppercase:
                    s = input('Cannot use uppercase letters in a name.\nPress <enter> to continue...')
                    upper = True
                    break
            if upper:
                continue

            # if the constant already exists, edit or delete it
            if name in user_dict.keys():
                print("\nEnter new value to redefine ", name, ".", sep='')
                print('Enter no value to delete ', name, ".", sep='')
            # make sure name is not a "system" name
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
                value = input('Value: ')
                if value != '':
                    try:
                        value = float(value)
                    except:
                        value = value.strip()
                        # if user put commas in a number, strip them
                        try:
                            value = float(value.replace(',', ''))
                        except ValueError:
                            pass
                
            # if you enter no name and no value, then exit...
            if not name and value == '':
                break

            # if you gave a name, but enter no value, then offer to delete name
            if name:
                if name in user_dict.keys() and value == '':
                    ok_delete = input('Delete ' + name + '? (Y/N) ')
                    if ok_delete.upper() == 'Y':
                        del user_dict[name]
                    break
                elif (not name in user_dict.keys()) and value == '':
                        txt = '\nWhen you enter no value, it is presumed you want\nto delete the name "' + \
                            name + '". However, no such name\nexists. Press <enter> to continue...'
                        s = input(txt)
                else:
                    pass

            # if you entered a name and a value, get a description
            if name and value != '':
                description = input("Description (optional): ")
                break

        # if you entered a name and a value (description is optional), update {user_dict}
        if name and value != '':
            user_dict.update({name: (value, description)})

        if not name and value == '':
            break

        repeat = ''
        while repeat.upper() not in ['Y', 'N']:
            repeat = input("Add or edit another constant? (Y/N): ")
        if repeat.upper() == 'N':
            break

    with open('constants.json', 'w+') as file:
        file.write(json.dumps(user_dict, ensure_ascii=False))

    print('\n', '='*10, ' USER-DEFINED CONSTANTS ', '='*11, sep='')
    for k, v in user_dict.items():
        print(k, ': ', v[0], ' ', v[1], sep='')
    print('='*45)

    return stack, user_dict


def get_user_expression_NOT_USED(stack, item):
    """
    Get a user-defined expression from the file containing user-defined constants. Execute the expression and place the result on the stack. This operation is particularly useful if you need to reuse a complicated expression with different stack values, making this a rudimentary programmable calculator.
    
Usage:

(1) To create and save an expression, type:

    user
    
 An expression is most often something you might enter on the command line, such as

    (3 4 +) (5 4 +) *
    
Or, you can use x:, y:, z:, t: in your expression to refer to specific registers in the stack.

(2) To use your expression, type the expressions name

Example, using register names:

    (x: y: +) y: *
    
NOTE: Keep in mind that during evaluation of the expression, the stack contents change as operations are executed. We'll see this happen in this example...

-- Let's put the following values on the stack.

    z:          7.0000
    y:          3.0000
    x:          1.0000

-- When the expression is run, the + operator adds x: and y:. y: is removed and x: is replaced with the result: 4. z: drops down to the y: register:

    z:          0.0000
    y:          7.0000
    x:          4.0000

-- Then the current x: and y: are multiplied and the result, 28, is put in the x: register:

    z:          0.0000
    y:          0.0000
    x:         28.0000

NOTE: 
(1) The non-obvious point is that, in an expression, the registers (e.g., "x:") are not variable names, but refer to the stack at THAT point in the expression's execution.

(2) Simple use of register names can save a lot of time when repeating simple calculations, such as getting the mid-point between two values. Create and save the following expression, say as "mid". 

    y: x: s dup rd - 2 / s d +

Put any two values on the stack, and run the expression by typing:

    mid

An easy way to get the expression: use the command line to do what you need, then copy the steps from the tape. Format into one line, if needed, and then paste in the VALUE field when you create the user-defined expression using:

    user

(2) Memory registers can act as variables, and may be better suited for some complicated expressions. See help for M+, M-, MR, and ML.
    """
    try:
        with open("constants.json") as file:
            user_dict = json.load(file)
    except:
        user_dict = {}

    user_expression = ''
    if not user_dict:
        print('No expressions available.')
    elif item in user_dict.keys():
        print('\n', '='*10, ' USER-DEFINED EXPRESSIONS ', '='*11, sep='')
        for k, v in user_dict.items():
            print(k, ': ', v[0], ' ', v[1], sep='')
        print('='*45)
        user_expression = user_dict[item][0]

    return str(user_expression)


# === STACK FUNCTIONS =====

def drop(stack):
    """
    Drop the last element off the stack.\n\nExample: 
    4 3 d --> x: 4
    """
    stack.pop(0)
    return stack


def dup(stack):
    """
    Duplicate the last stack element. <TEENR> with nothing else on the command line will also duplicate x.\n\n
        
Examples (1):
    4 dup --> x: 4  y: 4
    
Example (2):
    4 <enter> <enter> --> y: 4  x: 4 
    """
    x = stack[0]
    stack.insert(0, x)
    return stack


def get_lastx(stack, lastx_list):
    """
    Put the last x: value on the stack.
    
Examples:
    4 5 ^ --> x: 1024
    
    lastx --> y: 1024  x: 5
    
    3 4 lastx --> z: 3  y: 4  x: 4 (duplicates x:)
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
    Display the tape (a running record of all expressions) from the current session.
    """
    if tape:
        tape = tape[0:-1] if tape[-1] == 'tape' else tape
    print('='*19, ' TAPE ', '='*20, sep='')
    ndx = 0
    while True:
        try:
            if tape[ndx] not in ['about', 'com', 'con', 'const', 'list', 'index', 'math', 'set', 'short', 'user', 'usercon', 'c', 'q', 'u', ]:
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
    Roll the stack up. x:-->y:, y:-->z:, z:-->t:, and t: wraps around to become x:.
    """
    x, y, z, t = stack[0], stack[1], stack[2], stack[3]
    stack[0], stack[1], stack[2], stack[3] = t, x, y, z

    return stack
    
    
def roll_down(stack):
    """
    Roll the stack down. t:-->z:, z:-->y:, y:-->x:, and x: wraps around to become t:.
    """
    x, y, z, t = stack[0], stack[1], stack[2], stack[3]
    stack[0], stack[1], stack[2], stack[3] = y, z, t, x
    return stack


def round_y(stack):
    """
    Round y: by x:.\n\nExample 3.1416 2 r --> x: 3.14
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
    Splits x: into integer and decimal parts.\n\nExample: 3.1416 split --> y: 3  x: 0.1416
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
        err = "Standard deviation requires at least two non-zero data points."
        print('      St. dev: not computed')

    print('      Minimum:', fs.format(minimum))
    print('      Maximum:', fs.format(maximum))
    print('          Sum:', fs.format(sm))
    if err: print('\n', err, '\n', sep='')

    print('='*45)
    print("Zero values 'above' the first non-zero element in\nstack were ignored. Use <list> to inspect stack.", sep='')
    return stack


def swap(stack):
    """
    Swap x: and y: values on the stack.
    
Example (1): 
    3 4 swap --> y: 4  x: 3
    
Example (2):
    4 3 s --> y: 3  x: 4

Note that example (2) uses a shortcut. To list shortcuts, type: 

    short
    """
    stack[0], stack[1] = stack[1], stack[0]
    return stack


def trim_stack(stack):
    """
    Remove all elements on the stack except the x:, y:, z:, and t: registers.
    
Note: You can use 

    list

to inspect the entire stack.
    """
    stack = stack[0:4]
    print()
    return stack


# === COLOR FUNCTIONS ====

def hex_to_rgb(stack, item):
    """
    Convert hex color to rgb.

Example: 
    #b31b1b rgb --> z: 179  y: 27  x: 27
    
NOTE: to detect a hex value, the string you enter must begin with '#'.
    """
    if item[0] == '#':
        item = item[1:]
        try:
            r, g, b = int(item[0:2], 16), int(item[2:4], 16), int(item[4:6], 16)
        except ValueError:
            print('='*45)
            print('Not a valid hex color.')
            print('='*45)
            return stack

        stack.insert(0, r)
        stack.insert(0, g)
        stack.insert(0, b)
    else:
        print('='*45)
        print('You must provide a hex value.\nExample: #b31b1b')
        print('='*45)
    return stack


def rgb_to_hex(stack):
    """
    Convert rgb color (z:, y:, x:) to hex color.
    
Example:
    179 27 27 hex --> #b31b1b

    """
    r, g, b = int(stack[2]), int(stack[1]), int(stack[0])
    c = list(range(0, 256))
    if r in c and g in c and b in c:
        print('='*45)
        print('#' + str(hex(r)[2:]) + str(hex(g)[2:]) + str(hex(b)[2:]))
        print('='*45, '\n', sep='')
    else:
        print('='*45)
        print('r, g, or b not in the\nrange of 0 to 255.')
        print('='*45)

    return stack


def get_hex_alpha(stack):
    """
    Put a percent alpha value (between 0 and 100) in x:; this operation returns the hex equivalent, reported as a string.

Example:
    75 alpha --> BF
    """
    if stack[0] >= 0 and stack[0] <= 100:
        n = str(int(stack[0]))
        print('='*45)
        print('alpha:', alpha[n])
        print('='*45)
    else:
        print('='*45)
        print("Alpha value must be between 0 and 100.")
        print('='*45)

    return stack


def list_alpha(stack):
    """
    List alpha values and their hex equivalents.
    """
    print('\n', '='*15, ' ALPHA VALUES ', '='*16, sep='')
    for k, v in alpha.items():
        print('{:>3}'.format(k), ": ", v, sep='')
    print('='*45)
    return stack


# === COMMON CONVERSIONS ====

def inch(stack):
    """
    Convert cm to inches.\n\nExample:
        
    2.54 inch --> x: 1 (converts 2.54 cm to 1 inch)
    """
    # 1 in = 2.54 cm
    stack[0] = stack[0] / 2.54
    return stack


def cm(stack):
    """
    Convert inches to cm.\n\nExample:
        
    1.00 cm --> 2.54 (converts 1 inch to 2.54 cm)
    """
    # 1 in = 2.54 cm
    stack[0] = stack[0] * 2.54
    return stack


def lengths(stack):
    """
    Convert a decimal measurement to a fraction. For example, you can easily determine what is the equivalent measure of 2.25 inches in eighths. Very handy for woodworking.
    
Example (1)
    2.25 8 i --> t: 2.25  z: 2  y: 2  x: 8
    
Translation, reading z-->x:
    2.25 inches = 2 2/8"
    
Example (2)
    3.65 32 i --> t: 3.65  z: 3  y: 20.8  x: 32
    
Translation,, reading z-->x:
    3.65 inches = 3 20.8/32"
    
Example (3)
    Enter: 3.25 then 8i
    Returns: t,z,y,z... 3.25, 3, 2, 8

Translation, reading z-->x:
    3.25" =  3 2/8"
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
    Convert temperature from F to C.\n\nExample:
        
    212 fc --> x: 100
    """
    # e.g.: enter 32 ftco and return 0
    # C = (5/9)*(°F-32)
    result = 5 / 9 * (stack[0] - 32)
    stack.pop(0)
    stack.insert(0, round(result, 1))
    return stack


def ctof(stack):
    """
    Convert temperature from C to F.\n\nExample:
        
    100 cf --> x: 212
    """
    # e.g.: enter 0C ctof and return 32F
    # F = (9/5)*(°C)+32
    result = ((9 / 5) * stack[0]) + 32.0
    stack.pop(0)
    stack.insert(0, round(result, 1))
    return stack


def go(stack):
    """
    Convert weight from grams to ounces.\n\nExample:
        
    453.5924 go --> x: 16
    """
    # e.g.: enter 16g and return 453.59237
    stack[0] = stack[0] * 16.0 / 453.59237
    return stack


def og(stack):
    """
    Convert weight from ounces to grams.\n\nExample:

    16 og --> 453.5924 (grams)
    """
    # e.g.: enter 16g and return 453.59237
    stack[0] = stack[0] * 453.59237 / 16.0
    return stack


# MEMORY STACK FUNCTIONS ====================

def mem_add(stack, mem):
    """
    Add x: to y: memory register. 
    
Example: 
    1 453 
    M+ 

adds 453 to the current value of the #1 memory register.

Type:

    ML

to inspect (list) the memory registers.
    """
    # memory registers range from 1 to infinity
    if float(stack[1]) == int(stack[1]) and stack[1] > 0:
        register, register_value = stack[1], stack[0]
    else:
        print('='*45)
        print('Register numbers are positive integers, only.')
        print('='*45)
        return mem

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
    Subtract x: from y: memory register. If y: is not an integer, it will be converted to the next higher integer value to determine the target memory register for this operation.
    
Example:
    1 12 
    M- 
    
Subtracts 12 from the current value of the #1 memory register.

Type:

    ML

to inspect (list) the memory registers.
    """
    # memory registers range from 1 to infinity
    if float(stack[1]) == int(stack[1]) and stack[0] > 0:
        register, register_value = stack[1], stack[0]
    else:
        print('='*45)
        print('Register numbers are positive integers, only.')
        print('='*45)
        return mem

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
    Puts the value in the x: register value on the stack. If x: is not an integer, it will be converted to the next higher integer value to determine the target memory register for this operation.
    
Example: 
    3 MR
    
puts the value of the #3 memory register on the stack.

Type:

    ML

to inspect (list) the memory registers.
    """
    if float(stack[1]) == int(stack[1]) and stack[0] > 0:
        register = stack[0]
    else:
        print('='*45)
        print('Register numbers are positive integers, only.')
        print('='*45)
    # first, make sure the register exists in {mem}
    if register in mem.keys():
        stack.pop(0)
        stack.insert(0, mem[register])
    else:
        print('='*45)
        print('Memory register', str(int(stack[0])), 'does not exist.')
        print('Use\n\n\tML\n\nto list registers.')
        print('='*45)

    return stack


def mem_list(stack, mem):
    """
    List all elements of memory register.
    """
    # dictionaries are not sorted, so temporarily 
    # sort {mem} by key (register number)
    sorted_mem = dict(sorted(mem.items()))

    print('\n', '='*15, ' MEMORY STACK ', '='*16, sep='')
    for k, v in sorted_mem.items():
        print('Register ', int(k), ': ', v, sep='')
    print('='*45, sep='')


def mem_del(stack, mem):
    """
    Delete one, or a range, of memory registers. If x: (or y:) is not an integer, it will be converted to the next higher integer value to determine the target memory register for this operation. When deleting a range of registers, the order of the register numbers on the stack does not matter.

NOTE: Make sure the stack is clear before entering register numbers since, pending confirmation, this operation uses whatever numbers appear in x: and y: as the range of registers to delete.

Example (1):
    1 MD --> deletes #1 memory register

Example (2):
    10 3 MD --> deletes memory register #3 to #10, inclusive

Example (3):
    4 MD --> deletes memory register 4; if a value was left accidentally in y:, then a range of registers will be deleted. Confirmation before deletion prevents disaster.

Type:

    ML

to inspect (list) the memory registers.
    """
    register1, register2 = 0, 0

    # delete a single register: register2
    # delete a range: between register1 and register2, inclusive
    if math.ceil(stack[0]) >= 1:
        register1 = math.ceil(stack[0])
    else:
        print('='*45)
        print('Register numbers are positive integers, only.')
        print('='*45)
    if math.ceil(stack[1]) >= 1:
        register2 = math.ceil(stack[1])
    elif stack[1] == 0:
        pass # keeps register2 == 0
    else:
        print('='*45)
        print('Register numbers are positive integers, only.')
        print('='*45)

    # make sure register2 is >= register1
    if register1 > register2:
        register1, register2 = register2, register1

    # if you only want to delete 1 register, then register1 will be -0- and we will delete register2
    if register1 == 0:
        print('Are you sure you want to delete')
        confirm = input('register ' + str(register2) + '? (Y/N) ')
        if confirm.upper() == 'N':
            stack.pop(0)
            return stack, mem
        if register2 in mem:
            stack.pop(0)
            del mem[register2]
        
    else:
        print('Are you sure you want to delete')
        confirm = input('register ' + str(register1) + ' to register ' + str(register2) + '? (Y/N) ')
        if confirm.upper() == 'N':
            stack.pop(0)
            stack.pop(0)
            return stack, mem
        else:
            # remove registers between register1 and register2, inclusive
            for i in range(register2, register1-1, -1):
                if i in mem:
                    del mem[i]
            stack.pop(0)
            stack.pop(0)
        
    return stack, mem


# HELP ====================

def help(stack):
    """
  <basics>: the basics of RPN
<advanced>: how to use THIS calculator

You can also type:

    h [command] 

to get information about a specific command.
"""

    txt = """
=================== HELP ====================
<basics> : the basics of RPN
<advanced> : how to use THIS calculator

You can also type:

    h [command]

to get information about a specific command. Example:

    h help
============================================="""

    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack
    

def basics(stack):
    """
    The basics of RPN.
    
Type:

    basics
    
to display an introduction to how RPN calculators work.
    """
    txt = """
============= HELP: RPN BASICS ==============
An RPN calculator has no "equals" < = > key. Rather, numbers are placed on a "stack" and then an operation is invoked to act on the stack values. The result of the operation is placed back on the stack.
            
EXAMPLE:
                
Type: 
    
    3 <enter>      4 <enter>

Result:

    y:          3.0000
    x:          4.0000
            
When 3 is entered, it goes to the x: register. Then, when 4 is entered, 3 is moved to the y: register and 4 is placed in the x: register. Now, you can do anything you want with those two numbers. Let's add them.
            
Type: 

    + <enter>
            
The x: and y: registers are added, and the result (7) appears on the stack.
        
The speed of RPN is realized when entering expressions:
            
Type: 

    3 4 dup + +
            
ada parses the whole expression at once. After "dup", the stack looks like this:

    t:          0.0000
    z:          3.0000
    y:          4.0000
    x:          4.0000

The first + adds y: and x: 

    t:          0.0000
    z:          0.0000
    y:          3.0000
    x:          8.0000

The second + adds y: and the new x:

    t:          0.0000
    z:          0.0000
    y:          0.0000
    x:         11.0000

You can also group items using parentheses (nested groups are allowed!). 

Example: 

    (145 5+)(111 20+) * 

Parentheses make sure that operations are applied as you intend. The result of the first group is placed on the stack in x:. Then it is moved to y: when the second group is executed and placed in x:. Then the multiplication operator multiplies x: and y:. This type of operation is where the real power of RPN is realized. 
============================================="""
        
    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack


def advanced(stack):
    """
    Advanced help: how to use this calculator: ada.
    
Type:

    advanced
    
for information about advanced use of RPN and, in particular, this command-line calculator.
    """
    txt = """ 
=========== HELP: HOW TO USE ada ============
You can get a list of available operations  by typing:

    index

or more detailed information by typing:

    h [command]

where [command] is any command in the lists of commands, operations, and shortcuts. All of the common calculator operations are available.

Numbers entered in a sequence MUST be separated by spaces, for obvious reasons. A single shortcut can follow a number directly, but sequences of shortcuts or operations using words must use spaces. For examples of valid and invalid expressions, put the following numbers on the stack:

    t:          0.0000
    z:          4.0000
    y:          7.0000
    x:          3.0000

We want to drop 3, swap 4 and 7, then get the square root of the x: register (4), to yield the result: 2.0. Valid and invalid expressions:

    (1) 4 7 3 d s sqrt (valid)
    (2) 4 7 3d s sqrt  (valid)
    (3) 4 7 3ds sqrt   (invalid)
    (4) 4 7 3 dssqrt   (invalid)

Except for functions related to the memory registers (M+, MR, etc.), commands/operators use lower case only. Not having to use the <shift> key increases speed of entry.

ada keeps track of expressions you use, and these can be displayed by typing: 

    tape

The tape provides a running list of expressions entered during the current session. You can use the up and down arrow keys to cycle through items you have entered. Optionally, the tape can be displayed after every operation through "settings".

Besides the stack, ada provides three other features of interest. Type:

    h [related commands]

for more detailed information.

1. Memory register, where you can store, add, subtract, and recall numbers. Access these registers by their number. [related commands: M+, M-, MR, MD, and ML]

2. User-defined constants, where you can store constants, or even whole expressions, by name. These are saved between sessions. [related commands: user, usercon]

3. Conversion between RGB and hex colors, including alpha values. [related commands: alpha, rgb, and hex]

There's more! Explore the index and h [command] to see more of ada's capabilities.
============================================="""

    print('\n'.join([fold(txt) for txt in txt.splitlines()]))

    return stack


def fold(txt):
    """
    Textwraps 'txt'; used by help_fxn(), help(), basics(), and advances().
    """
    return textwrap.fill(txt, width=45)


def help_fxn(stack, item):
    """
    Help for a single command.
    
Example:

    h sqrt --> Find the square root of x.
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
    
    return stack


# GLOBAL FUNCTIONS AND RUN RPN() ====================

if __name__ == '__main__':

    version_num = '2.4 rev??'

    print('ada ' + version_num[0:3] +  ' - an RPN calculator')

    # initialize the x, y, z, and t registers, and other global variables
    stack, entered_value = [0.0], 0.0
    lastx_list, mem, tape = [0.0], {}, []
    letters = ascii_letters + '_' + ':'
    lower_letters = ascii_lowercase + '_' + ':'

    # initial setup by saving default settings to config.json
    # if the file already exists, then put contents in {settings}
    try:
        with open("config.json", 'r') as file:
            settings = json.load(file)
    except FileNotFoundError:
        settings = {
            'show_menu': 'Y',
            'dec_point': '4',
            'separator': ',',
            'show_tape': 'N',
            'show_tips': 'Y',
            }
        # if config.json does not exist, create it
        with open('config.json', 'w+') as file:
            file.write(json.dumps(settings, ensure_ascii=False))
        
    # menu gets printed on screen 4 items to a line
    menu = ( 
        '<d>rop       ', '<s>wap       ', '<r>oll <u>p  ', '<r>oll<d>own',
        '<n>eg        ', '<c>lear      ', '<usercon>stants', '',
        '<set>tings   ', '<index>     ', '<h> [...]    ', '<q>uit       '
        )

    # operations that modify or use x: only (stack[0])
    op1 = {
        "": ('', ''),
        "====": ('', '==== GENERAL ==========================='),
        "abs": (absolute, "absolute value of x:"),
        "ceil": (ceil, "6.3->7"),
        "!": (factorial, "x: factorial"),
        "floor": (floor, "6.9->6"),
        "log": (log, "log10(x:)"),
        "n": (negate, "negative of x:"),
        # "negate": (negate, "Get the negative of x."),
        "pi": (pi, "pi"),
        "rand": (random_number, 'random int between x: and y:.'),
        "round": (round_y, 'round y: by x:'),
        "sqrt": (square_root, "sqrt(x:)"),
        " ": ('', ''),
        " ====": ('', '==== TRIGONOMETRY ======================'),
        "cos": (cos, "cos(x:) -- x: must be radians"),
        "sin": (sin, "sin(x:) -- x: must be radians"),
        "tan": (tan, "tan(x:) -- x: must be radians"),
        "acos": (acos, "acos(x:) -- x: must be radians"),
        "asin": (asin, "asin(x:) -- x: must be radians"),
        "atan": (atan, "atan(x:) -- x: must be radians"),
        "deg": (deg, "convert angle x: in radians to degrees"),
        "rad": (rad, "convert angle x: in degrees to radians"),
        "  ": ('', ''),
        "  ====": ('', '==== CONVERSIONS ======================='),
        'decbin': (convert_dec_to_bin, 'Convert x: from decimal to binary.'),
        "bindec": (convert_bin_to_dec, 'Convert x: from binary to decimal.'),
        "dechex": (convert_dec_to_hex, 'Convert x: from decimal to hex.'),
        "hexdec": (convert_hex_to_dec, 'Convert x: from hex to decimal.'),
        'cm': (cm, 'Convert inches to centimeters.'),
        'inch': (inch, 'Convert centimeters to inches.'),
        'cf': (ctof, 'Convert centigrade to Fahrenheit.'),
        'fc': (ftoc, 'Convert Fahrenheit to centigrade.'),
        'go': (go, 'Convert weight from grams to ounces.'),
        'og': (og, 'Convert weight from ounces to grams.'),
        'i': (lengths, 'Convert decimal measure to fraction.'),
    }

    # operations that require both x: and y: (stack[0] and stack[1])
    op2 = {
        "    ": ('', ''),
        "====": ('', '==== STANDARD OPERATORS ================'),
        "+": (add, "y: + x:"),
        "-": (sub, "y: - x:"),
        "*": (mul, "y: * x:"),
        "x": (mul, "y: * x:"),
        "/": (truediv, "y: / x:"),
        "%": (mod, "remainder from division"),
        "^": (pow, "y: ** x:"),
    }

    # general commands that provide function beyond math operators
    commands = {
        "      ====": ('', '==== GENERAL ==========================='),
        "about": (about, "Info about the author and product."),
        "import": (get_file_data, "Import data from a text file."),
        'set': (calculator_settings, 'Access and edit settings.'),
        'version': (version, 'Report the version number as a string.'),
        "     ": ('', ''),
        " ====": ('', '==== COLOR ============================='),
        'alpha': (get_hex_alpha, 'Hex equivalent of RGB alpha value.'),
        'hex': (rgb_to_hex, 'Convert rgb color (z:, y:, x:) to hex color.'),
        "list_alpha": (list_alpha, "List all alpha values."),
        'rgb': (hex_to_rgb, 'Convert hex color to rgb.'),
        "      ": ('', ''),
        "  ====": ('', '==== HELP =============================='),
        'help': (help, 'How to get help.'),
        "index": (manual, "Menu to access parts of the manual."),
        "basics": (basics, "The basics of RPN."),
        "advanced": (advanced, 'Advanced help: how to use ada.'),
        "com": (print_commands, "List all commands and math operations."),
        "math": (print_math_ops, "List math operations."),
        "con": (print_constants, 'List constants and conversions.'),
        "short": (print_shortcuts, 'Available shortcut functions.'),
        "       ": ('', ''),
        "   ====": ('', '==== MEMORY REGISTERS =================='),
        "M+": (mem_add, 'Add x: to y: memory register.'),
        "M-": (mem_sub, 'Subtract x: from y: memory register.'),
        "MR": (mem_recall, 'Put x: register value on stack.'),
        "MD": (mem_del, 'Delete one or all memory registers.'),
        "ML": (mem_list, 'List elements of memory register.'),
        "        ": ('', ''),
        "    ====": ('', '==== STACK MANIPULATION ================'),
        "clear": (clear, "Clear all elements from the stack."),
        "drop": (drop, "Drop the last element off the stack."),
        "dup": (dup, "Duplicate the last stack element."),
        "lastx": (get_lastx, "Put the lastx value on the stack."),
        "list": (list_stack, "Show the entire stack."),
        "rolldown": (roll_down, "Roll stack down."),
        "rollup": (roll_up, "Roll stack up."),
        "split": (split_number, "Splits x: into integer and decimal parts."),
        'stats': (stats, 'Summary stats (non-destructive).'),
        "swap": (swap, "Swap x: and y: values on the stack."),
        'tape': (print_tape, "Display tape from current session."),
        "trim": (trim_stack, 'Remove stack, except the x:, y:, z:, and t:.'),
        "         ": ('', ''),
        "     ====": ('', '==== USER-DEFINED ======================'),
        "usercon": (print_dict, "List user-defined constants."),
        "user": (define_constant, 'Add/edit user-defined constant.'),
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
        'h': (help, 'Help for a single command.'),
        'n': (negate, 'Negative of x:'),
        'q': ('', 'Quit.'),
        'r': (round_y, 'round y by x:'),
        'rd': (roll_down, 'Roll the stack down.'),  
        'ru': (roll_up, 'Roll the stack up.'),  
        's': (swap, 'Swap x: and y: values on the stack.'),
            }

    # keys are "percent transparency" and values are "alpha code" for hex colors; 0% is transparent; 100% is no transparency
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
        with open("constants.json", 'r') as file:
            user_dict = json.load(file)
    except FileNotFoundError:
        user_dict = {}

    stack = RPN(stack, user_dict, lastx_list, mem, settings, tape)

    # the following line if for the developer only
    # stack = print_all_functions(stack, user_dict)
