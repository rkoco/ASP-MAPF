import sys
import clingo
import json
import time
import traceback
import signal
from threading import Thread
from time import sleep
import os


class IncrementalSolver:

    def __init__(self, minimum_time, num_agents, min_sum, total_cost, makespan_relax, opt_penalty, parse_path):
        self.minimum_time = minimum_time
        self.min_sum = min_sum
        self.total_cost = total_cost
        self.resp = []
        self.num_agents = num_agents
        self.sol_time = -1
        for a in range(self.num_agents):
            self.resp.append([])

        self.stats = None
        self.solved = False
        self.error = False
        
        self.first_makespan = -1
        self.opt_makespan = -1
        self.theoric_makespan = -1
        self.makespan = -1
        
        self.first_runtime = 0

        self.sol_cost = -1
        self.ground_time = 0

        self.solve_time = 0
        self.init_time = 0
        self.makespan_relax = makespan_relax
        self.opt_penalty = opt_penalty
        self.parse_path = parse_path


    def main(self, ctl, files):
        self.run_standard(ctl, files)

    def run_standard(self, ctl, files):
        if len(files) > 0:
            for f in files:
                ctl.load(f)
        else:
            ctl.load("-")
        
        step = 0
        while step <= self.minimum_time:
            for a in range(self.num_agents):
                self.resp[a].append((0,0))
            step += 1
        
        
        self.init_time = time.time()
        
        try:
            ctl.ground([("base", [])])
            self.ground_time = time.time() - self.init_time
        except:
            self.ground_time = time.time() - self.init_time
            self.solve_time = -1
            self.error = True
            return        


        self.init_time = time.time()
        print('grounded: {0}'.format(self.ground_time))
        

        ret = None
        try:
            ret = ctl.solve(on_model=self.on_model)
        except:
            self.solve_time = time.time() - self.init_time
            self.error = True
            return

        if ret is not None and ret.satisfiable:
            self.solved = True
            self.stats = ctl.statistics
            if self.opt_penalty:
                self.sol_cost = self.minimum_time * self.num_agents + ctl.statistics['summary']['costs'][0]
            else:
                self.sol_cost = ctl.statistics['summary']['costs'][0]
            
            print('sic:', self.total_cost, 'optimization:',ctl.statistics['summary']['costs'][0], 'sol_cost:',self.sol_cost,'makespan:', self.minimum_time, 'agents:', self.num_agents)
            imax = self.makespan_relax + self.sol_cost - 1 - self.total_cost
            if imax < self.minimum_time:
                imax = self.minimum_time

            self.theoric_makespan = imax


    def on_model(self,m):
        self.solve_time = time.time() - self.init_time
        
        if self.parse_path:
            for sym in m.symbols(shown=True):
                if sym.name == 'at':
                    args = sym.arguments
                    #print(args)
                    robot = int(args[0].number)
                    self.resp[robot][args[3].number] = (args[1].number,args[2].number)
