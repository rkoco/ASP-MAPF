import os
import clingo
import asp_solver
import lp_generator
import json
import locale
import time
import sys
import subprocess
import argparse


'''
Cambiar esto según la cantidad de problemas:
init -> numero inicial de agentes/obstaculos
step -> numero en que se incrementa el numero de agentes
num_problems -> numero de tipos de problemas
'''

init = 20
step = 2
num_problems = 26

def run_test(instances_folder, base_path, num_instances, results_path, penalty_type):
    opt_makespans = []

    with open(results_path, 'w') as results:
        results.write('sep=;\n')
        results.write('Instance;cost_relax;makespan_relax;First_solved;solved;;'
            '1stOPT;1stSOL-COST;1stMakespan;1stTheoricMakespan;1stRunTime;1stGroundTime;1stGroundPerc;1stAtoms;1stBodies;1stRules;1stTotal;;'
            'OPT;SOL-COST;Makespan;TheoricMakespan;RunTime;GroundTime;GroundPerc;Atoms;Bodies;Rules;Total\n')

        print(base_path.split('/')[-1])
        results.flush()

    
    num_list = []
    for x in range(num_instances):
        num_list.append(init+(x*step))
    print(num_list)

    for x in num_list:
        for y in range(num_instances):
            # Cambiar esto según el formato del nombre de las instancias
            instance_name = 'Instance-20-10-{0}-{1}'.format(x,y)
            path = '{0}/{1}'.format(instances_folder, instance_name)
            print('python run_problem.py -b {0} -p {1} -r {2} -i {3} -m 0'.format(base_path, penalty_type, results_path, path))
            p = subprocess.Popen('python run_problem.py -b {0} -p {1} -r {2} -i {3} -m 0'.format(base_path, penalty_type, results_path, path), shell=True)
            sys.stdout.flush() 
            retval = p.wait()
            print(retval)     


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base_path', help='Path of the base in asp, example: bases/baseE.lp', required=True)
    parser.add_argument('-p', '--penalty_type', help='A number: 0 or 1. 0 to indicate that the base is using grid dependent cost optimization, when using baseA and baseB select this.'
        + ' 1 to indicate that is using grid independent cost optimization when using baseC, baseD and baseE select this', required=True)
    parser.add_argument('-r', '--results_path', help='Path of the result file in csv, example: results.csv', required=True)
    parser.add_argument('-i', '--instances_folder', help='Path of the problem instances folder, example: problems/grid20_ag', required=True)
    parser.add_argument('-n', '--num_instances', help='Number of instances of each type of problem, for all the folders in this code is 10')
    
    args = parser.parse_args()

    instances_folder = args.instances_folder
    base_path = args.base_path
    results_path = args.results_path
    penalty_type = args.penalty_type


    num_instances = 10
    if args.num_instances:
        num_instances = int(args.num_instances)

    run_test(instances_folder, base_path, num_instances, results_path, penalty_type)

    

