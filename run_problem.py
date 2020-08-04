import sys
import clingo
import asp_solver
import lp_generator
import time
import traceback
import argparse



def run_problem(instance_path, base_path, results_path, penalty_type, results_mode):
    write_type = 'a'
    if results_mode:
        write_type = 'w'

    with open(results_path, write_type) as results:
        if results_mode:
            results.write('sep=;\n')
            results.write('Instance;cost_relax;makespan_relax;First_solved;solved;;'
                '1stOPT;1stSOL-COST;1stMakespan;1stTheoricMakespan;1stRunTime;1stGroundTime;1stGroundPerc;1stAtoms;1stBodies;1stRules;1stTotal;;'
                'OPT;SOL-COST;Makespan;TheoricMakespan;RunTime;GroundTime;GroundPerc;Atoms;Bodies;Rules;Total\n')
            results.flush()

        
        problem = lp_generator.Problem(50)
        print('reading instance')
        problem.read_instance(instance_path)
        print('generating solution')
        problem.gen_solution()
        
        buffer_path = 'buffer'
        problem.write_to_lp(buffer_path)
        
        print('Solving with clingo...')

        start_time = time.time()
        ms_max = problem.max_time
        ground_time = 0
        ground_time0 = 0
        runtime = 0
        runtime0 = 0

        makespan_relax = ms_max + 1
        ms0 = ms_max
        cost_relax = problem.total_cost
        first_solved = False
        solved = False


        solv0 = None
        solv = None

        curr = 300

        elapsed_real = 0

        try:
            while True:
                solv0 = asp_solver.IncrementalSolver(ms_max, problem.num_agents, problem.min_sum, problem.total_cost, ms0, penalty_type, False)
                clingo.clingo_main(solv0, [buffer_path, base_path , '--outf=3', '--opt-strat=usc,disjoint', '--time-limit={0}'.format(curr), '-t' ,'4','-c','bound={0}'.format(ms_max)])

                ground_time += solv0.ground_time
                elapsed_real += (solv0.solve_time + solv0.ground_time)

                if solv0.error:
                    break

                curr = int(300 - elapsed_real)
                if curr < 0:
                    break

                if solv0.sol_cost > 0:
                    runtime0 = elapsed_real
                    first_ms = ms_max + 1
                    ms_opt = int(solv0.theoric_makespan)
                    first_solved = True
                    ground_time0 = ground_time

                    if ms_opt == ms_max:
                        solv = solv0
                        solved = True
                        runtime = runtime0
                        final_ms = first_ms
                        break

                    solv = asp_solver.IncrementalSolver(ms_opt, problem.num_agents, problem.min_sum, problem.total_cost, ms0, penalty_type, True)
                    clingo.clingo_main(solv, [buffer_path, base_path,  '--outf=3', '--opt-strat=usc,disjoint', '--time-limit={0}'.format(curr),'-t' ,'4','-c','bound={0}'.format(ms_opt)])

                    ground_time += solv.ground_time
                    if solv.stats is not None:
                        runtime = elapsed_real + (solv.solve_time + solv.ground_time)
                        final_ms = check_makespan(solv.resp)
                        summary = solv.stats['summary']
                        solved = True
                    break
                ms_max += 1
        except:
            print(traceback.format_exc())

    
        row = [instance_path]
        row.append(cost_relax)
        row.append(makespan_relax)

        if first_solved:
            row.append(1)
            row.append(0)
            row.append('\t')

            row.append(format_float(solv0.stats['summary']['costs'][0]))
            row.append(format_float(solv0.sol_cost))
            row.append(first_ms)
            row.append(int(solv0.theoric_makespan) + 1)
            row.append(format_float(runtime0))
            row.append(format_float(ground_time0))
            row.append(format_float(ground_time0/runtime0*100))
            row.append(format_float(solv0.stats['problem']['lp']['atoms']))
            row.append(format_float(solv0.stats['problem']['lp']['bodies']))
            row.append(format_float(solv0.stats['problem']['lp']['rules']))
            row.append(format_float(solv0.stats['problem']['lp']['atoms'] + solv0.stats['problem']['lp']['bodies'] + solv0.stats['problem']['lp']['rules']))
            row.append('\t')

            if solved:
                row[4] = 1
                row.append(format_float(solv.stats['summary']['costs'][0]))
                row.append(format_float(solv.sol_cost))
                row.append(final_ms)
                row.append(int(solv.theoric_makespan) + 1)
                row.append(format_float(runtime))
                row.append(format_float(ground_time))
                row.append(format_float(ground_time/runtime*100))
                row.append(format_float(solv.stats['problem']['lp']['atoms']))
                row.append(format_float(solv.stats['problem']['lp']['bodies']))
                row.append(format_float(solv.stats['problem']['lp']['rules']))
                row.append(format_float(solv.stats['problem']['lp']['atoms'] + solv.stats['problem']['lp']['bodies'] + solv.stats['problem']['lp']['rules']))

        else:
            row.append(0)
            row.append(0)
        
        results.write(';'.join(map(str, row)) + '\n')
        results.flush()
            
def format_float(num):
    str_num = str(num)
    return str_num.replace(',', '.')

def check_makespan(sol):
    makespan = -1
    for ag in sol:
        last_x = -1
        last_y = -1
        step = 0
        wait_on_goal = 0
        for pos in ag:
            if last_x == pos[0] and last_y == pos[1]:
                wait_on_goal += 1
            else:
                wait_on_goal = 0

            last_x = pos[0]
            last_y = pos[1]

            step+=1

        ag_makespan = step - wait_on_goal
        if ag_makespan > makespan:
            makespan = ag_makespan

    return makespan

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base_path', help='Path of the base in asp, example: bases/baseE.lp', required=True)
    parser.add_argument('-p', '--penalty_type', help='A number: 0 or 1. 0 to indicate that the base is using grid dependent cost optimization, when using baseA and baseB select this.'
        + ' 1 to indicate that is using grid independent cost optimization when using baseC, baseD and baseE select this', required=True)
    parser.add_argument('-r', '--results_path', help='Path of the result file in csv, example: results.csv', required=True)
    parser.add_argument('-i', '--instance_path', help='Path of the problem instance file, example: problems/grid20_ag/Instance-20-10-40-5', required=True)
    parser.add_argument('-m', '--results_mode', help='A number: 0 or 1. 0 to indicate that the results file already exists and you want to append the results to that file.' 
        + '1 to indicate that you want to create a new file. By default this is 1')

    args = parser.parse_args()

    base_path = args.base_path   
    results_path = args.results_path
    instance_path = args.instance_path
    
    results_mode = True
    if args.results_mode and args.results_mode == '0':
        results_mode = False

    penalty_type_int = int(args.penalty_type)
    if penalty_type_int == 0:
        penalty_type = False
    else:
        penalty_type = True


    run_problem(instance_path, base_path, results_path, penalty_type, results_mode)
    