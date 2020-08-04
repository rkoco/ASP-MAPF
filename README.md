# ASP-MAPF

Multi agent pathfinding solver using asp/clingo

- Use run_problem.py to execute the solver for a single problem instance.
- Use tester.py to execute the solver for a problem folder.    
- Also gui.py contains a graphic interface to visualize the solution. To run it just execute python gui.py and do the following:
  * Click File > Open > Problem
  * Click Generate to create the clingo file (saved as buffer.lp)
  * Click Solve to generate the solution (can take some time)


*This code requires the clingo library installled: https://anaconda.org/potassco/clingo*
