Mutatest diagnostic summary
===========================
 - Source location: /Users/yashsalunke/Desktop/calcure-1/calcure/calendars.py
 - Test commands: ['/Users/yashsalunke/opt/anaconda3/bin/pytest', 'test_blackbox.py', 'test_whitebox.py', 'test_integration.py', 'test_mock.py', '-q']
 - Mode: f
 - Excluded files: []
 - N locations input: 10
 - Random seed: None

Random sample details
---------------------
 - Total locations mutated: 10
 - Total locations identified: 29
 - Location sample coverage: 34.48 %


Running time details
--------------------
 - Clean trial 1 run time: 0:00:00.487337
 - Clean trial 2 run time: 0:00:00.684889
 - Mutation trials total run time: 0:00:22.060625

Overall mutation trial summary
==============================
 - DETECTED: 44
 - SURVIVED: 1
 - TOTAL RUNS: 45
 - RUN DATETIME: 2026-04-17 23:09:45.361839


Mutations by result status
==========================


SURVIVED
--------
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Gt'>


DETECTED
--------
 - calcure/calendars.py: (l: 35, c: 8) - mutation from If_Statement to If_False
 - calcure/calendars.py: (l: 35, c: 8) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Eq'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Or'> to <class 'ast.And'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.NotEq'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 91, c: 16) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 91, c: 16) - mutation from If_Statement to If_False