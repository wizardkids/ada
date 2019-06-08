# **_ada_ - a command-line RPN calculator**

## **Why a command-line calculator?**
...because keyboard entry is so much faster than pointing and clicking or tapping buttons on a touch screen.</span>

## **Why RPN?** 
...because hitting an equals key is so 1995 and using RPN is demonstrably faster than a conventional calculator.

**_ada's exclusive goal_** is to provide an app that loads fast, executes fast, and is not bloated with capabilities that you will never use because there's Excel, Jupyter Notebooks, and SAS/STAT. For example, try this with any other kind of calculator:

    4 16 s 2 ^ 4 / /

With no more than single keys, and typing a single expression, **_ada_** executes the line to result in x: 4

## **Features:**
- standard RPN number entry and execution with an unlimited stack size
- easy access to lists of available commands, operators, and constants
- extensive help, including specific help for every command and operator
- ability to use parentheses to group expressions in a single line
- read single-column data from an external file
- save your own constants
- save your own expressions, with easy recall
- unlimited memory registers
- a tape records all expressions entered during the current session
- easy retrieval of previously entered expressions
- descriptive statistics for numbers on the stack
- ...and there's more!

## **Installation:**
Installation could not be easier. **_ada_** requires only one file: either `ada.py` or `ada.exe`. 

1. If you have python 3.7+ installed, you can download `ada.py` and, assuming python.exe is in your PATH, run:
   
    `python ada.py`

2. Download `ada.exe` and run the executable. No other files are needed.

3. Download `ada.py` and use [pyinstaller](https://www.pyinstaller.org/) (or equivalent) to build your own executable.

During the first run of **_ada_**, `config.json` and `constants.json` are created automatically. A .ico file is available if you want to create a shortcut with a unique icon.