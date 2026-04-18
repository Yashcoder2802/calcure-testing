Mutatest diagnostic summary
===========================
 - Source location: /Users/yashsalunke/Desktop/calcure-1/calcure/calendars.py
 - Test commands: ['/Users/yashsalunke/opt/anaconda3/bin/pytest', 'test_blackbox.py', 'test_whitebox.py', 'test_integration.py', 'test_mock.py', '-q']
 - Mode: f
 - Excluded files: []
 - N locations input: 9999
 - Random seed: None

Random sample details
---------------------
 - Total locations mutated: 29
 - Total locations identified: 29
 - Location sample coverage: 100.00 %


Running time details
--------------------
 - Clean trial 1 run time: 0:00:00.492502
 - Clean trial 2 run time: 0:00:00.433111
 - Mutation trials total run time: 0:01:05.080170

Overall mutation trial summary
==============================
 - DETECTED: 122
 - SURVIVED: 10
 - TOTAL RUNS: 132
 - RUN DATETIME: 2026-04-17 23:11:13.673870


Mutations by result status
==========================


SURVIVED
--------
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Eq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Eq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 49, c: 8) - mutation from If_Statement to If_False
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 91, c: 19) - mutation from <class 'ast.NotEq'> to <class 'ast.Gt'>


DETECTED
--------
 - calcure/calendars.py: (l: 35, c: 8) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 35, c: 8) - mutation from If_Statement to If_False
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 39, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.NotEq'>
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 39, c: 36) - mutation from <class 'ast.And'> to <class 'ast.Or'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Eq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Eq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Eq'> to <class 'ast.NotEq'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.Eq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 42, c: 21) - mutation from <class 'ast.And'> to <class 'ast.Or'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Eq'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.NotEq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 42, c: 40) - mutation from <class 'ast.Or'> to <class 'ast.And'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Eq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Eq'> to <class 'ast.NotEq'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Eq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 42, c: 59) - mutation from <class 'ast.Eq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 44, c: 20) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Gt'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.NotEq'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.Eq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 44, c: 36) - mutation from <class 'ast.And'> to <class 'ast.Or'>
 - calcure/calendars.py: (l: 49, c: 8) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 57, c: 22) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 57, c: 23) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 59, c: 28) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 60, c: 21) - mutation from <class 'ast.Mod'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 60, c: 22) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 66, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 70, c: 8) - mutation from If_Statement to If_False
 - calcure/calendars.py: (l: 70, c: 8) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 75, c: 32) - mutation from <class 'ast.Sub'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mult'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.FloorDiv'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Mod'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Pow'>
 - calcure/calendars.py: (l: 76, c: 23) - mutation from <class 'ast.Add'> to <class 'ast.Div'>
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Sub'>
 - calcure/calendars.py: (l: 76, c: 24) - mutation from <class 'ast.FloorDiv'> to <class 'ast.Add'>
 - calcure/calendars.py: (l: 91, c: 16) - mutation from If_Statement to If_False
 - calcure/calendars.py: (l: 91, c: 16) - mutation from If_Statement to If_True
 - calcure/calendars.py: (l: 91, c: 19) - mutation from <class 'ast.NotEq'> to <class 'ast.LtE'>
 - calcure/calendars.py: (l: 91, c: 19) - mutation from <class 'ast.NotEq'> to <class 'ast.GtE'>
 - calcure/calendars.py: (l: 91, c: 19) - mutation from <class 'ast.NotEq'> to <class 'ast.Lt'>
 - calcure/calendars.py: (l: 91, c: 19) - mutation from <class 'ast.NotEq'> to <class 'ast.Eq'>