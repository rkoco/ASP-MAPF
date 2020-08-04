import os
import clingo
import asp_solver
import json

class Problem:
    def __init__(self, time):
        self.obstacles = []
        self.map = []
        self.height = 0
        self.width = 0
        self.num_agents = 0
        self.agents_pos = []
        self.time = time
        self.max_distance = -1
        self.heuristic = []
        self.heuristic_initial = []
        self.best_dirs = []

        self.dirX = [1,0,-1,0]
        self.dirY = [0,1,0,-1]

        # Directions name for each (they are swapped because the search is done backwards)
        self.dir_name = ['left', 'down', 'right', 'up']
        self.instance_number = ''
        self.opt_sumtime = 0
        self.opt_timestep = -1

        self.sol = []
        self.max_time = -1
        self.total_cost = 0
        self.agent_cost = []
        self.min_sum = 0

        self.solved = False


    def read_instance(self, inp):
        with open(inp, 'r') as in_file:
            self.instance_number = in_file.readline().strip()
            in_file.readline()
            line = in_file.readline().strip().split(',')
            self.height = int(line[0])
            self.width = int(line[1])
            for y in range(self.height):
                line = in_file.readline().strip()
                row = []
                x = 0
                for cell in line:
                    if cell != '.':
                        row.append(1)
                        self.obstacles.append((y,x))
                    else:
                        row.append(0)

                    x+=1
                self.map.append(row)

            in_file.readline()
            self.num_agents = int(in_file.readline())
            for a in range(self.num_agents):
                agent_map = []
                agent_map_init = []
                agent_dirs = []
                for y in range(self.height):
                    agent_row = []
                    agent_row_init = []
                    row_dirs = []
                    for x in range(self.width):
                        agent_row.append(-1) #infty heuristic (not defined)
                        agent_row_init.append(-1)
                        row_dirs.append([])
                    agent_map.append(agent_row)
                    agent_map_init.append(agent_row_init)
                    agent_dirs.append(row_dirs)

                self.heuristic.append(agent_map)
                self.heuristic_initial.append(agent_map_init)
                self.best_dirs.append(agent_dirs)

                line = in_file.readline().split(',')
                pos = (int(line[3]),int(line[4]),int(line[1]),int(line[2]))
                self.agents_pos.append(pos)

    def read_map(self, inp):
        self.obstacles = []
        self.map = []
        with open(inp, 'r') as in_file:
            line = in_file.readline().split(',')
            self.height = int(line[0])
            self.width = int(line[1])

            y = 0
            for l in in_file.readlines():
                line = l.split(',')
                row = []
                x = 0
                for cell in line:
                    row.append(int(cell))

                    if int(cell) == 1:
                        obs = (y, x)
                        self.obstacles.append(obs)
                    x += 1
                y += 1
                self.map.append(row)

    def read_agents(self, inp):
        self.agents_pos = []
        with open(inp, 'r') as in_file:
            line = in_file.readline()
            self.num_agents = int(line)

            #Put heuristics (and best dirs) for each agent for each cell
            for i in range(self.num_agents):
                agent_map = []
                agent_map_init = []
                agent_dirs = []
                for y in range(self.height):
                    agent_row = []
                    agent_row_init = []
                    row_dirs = []
                    for x in range(self.width):
                        agent_row.append(-1) #infty heuristic (not defined)
                        agent_row_init.append(-1)
                        row_dirs.append([])
                    agent_map.append(agent_row)
                    agent_map_init.append(agent_row_init)
                    agent_dirs.append(row_dirs)

                self.heuristic.append(agent_map)
                self.heuristic_initial.append(agent_map_init)
                self.best_dirs.append(agent_dirs)

            for l in in_file.readlines():
                line = l.split(',')
                pos = (int(line[0]),int(line[1]),int(line[2]),int(line[3]))
                self.agents_pos.append(pos)

    def dijkstra_init(self, ag_id):
        posY = self.agents_pos[ag_id][0]
        posX = self.agents_pos[ag_id][1]

        obj = (posY, posX)
        open_list = []
        open_list.append(obj)
        self.heuristic_initial[ag_id][posY][posX] = 0
        while True:
            if not open_list:
                break
            u = open_list.pop(0)
            ux = u[1]
            uy = u[0]

            #Succesors
            for i in range(4):
                vx = ux + self.dirX[i]
                vy = uy + self.dirY[i]
                #Check if pos is valid:
                if vx < self.width and vx >= 0 and vy < self.height and vy >= 0 and self.map[vy][vx] != 1:
                    v_cost = self.heuristic_initial[ag_id][uy][ux] + 1
                    gv = self.heuristic_initial[ag_id][vy][vx]
                    if gv == -1 or v_cost < gv:
                        self.heuristic_initial[ag_id][vy][vx] = v_cost
                        #reset the list, there is a better path
                        open_list.append((vy,vx))


    def solve_agent(self, ag_id):
        posY = self.agents_pos[ag_id][2]
        posX = self.agents_pos[ag_id][3]

        obj = (posY, posX)
        open_list = []
        open_list.append(obj)
        self.heuristic[ag_id][posY][posX] = 0
        self.best_dirs[ag_id][posY][posX] = ['wait']
        while True:
            if not open_list:
                break
            u = open_list.pop(0)
            #print(u)
            ux = u[1]
            uy = u[0]

            #Succesors
            for i in range(4):
                vx = ux + self.dirX[i]
                vy = uy + self.dirY[i]
                #Check if pos is valid:
                if vx < self.width and vx >= 0 and vy < self.height and vy >= 0 and self.map[vy][vx] != 1:
                    v_cost = self.heuristic[ag_id][uy][ux] + 1
                    gv = self.heuristic[ag_id][vy][vx]
                    if gv == -1 or v_cost < gv:
                        self.heuristic[ag_id][vy][vx] = v_cost
                        #reset the list, there is a better path
                        self.best_dirs[ag_id][vy][vx] = []
                        self.best_dirs[ag_id][vy][vx].append(self.dir_name[i])
                        open_list.append((vy,vx))

                    if v_cost == gv:
                        #If the cost is the same, the new path is equivalent and also is a best move
                        self.best_dirs[ag_id][vy][vx].append(self.dir_name[i])


    def solve_position(self, xf, yf, depth):
        obj = (yf, xf)
        open_list = []
        open_list.append(obj)

        pos_costs = [[-1] * self.width for i in range(self.height)]
        pos_costs[yf][xf] = 0

        while True:
            if not open_list:
                break
            u = open_list.pop(0)
            ux = u[1]
            uy = u[0]

            #Succesors
            if pos_costs[uy][ux] >= depth:
                continue

            for i in range(4):
                vx = ux + self.dirX[i]
                vy = uy + self.dirY[i]
                
                #Check if pos is valid:
                if vx < self.width and vx >= 0 and vy < self.height and vy >= 0 and self.map[vy][vx] != 1:
                    v_cost = pos_costs[uy][ux] + 1
                    gv = pos_costs[vy][vx]
                    if gv == -1 or v_cost < gv:
                        pos_costs[vy][vx] = v_cost
                        #reset the list, there is a better path
                        open_list.append((vy,vx))
        return pos_costs
            

    def calc_time(self):
        self.opt_sumtime = 0
        self.opt_timestep = -1
        for ag in range(self.num_agents):
            posX = self.agents_pos[ag][0]
            posY = self.agents_pos[ag][1]
            best_time = self.heuristic[ag][posX][posY]
            if (self.opt_timestep == -1 or best_time > self.opt_timestep):
                self.opt_timestep = best_time

            self.opt_sumtime += best_time

        print(self.opt_timestep)


    def gen_solution(self):
        self.sol = []
        self.total_cost = 0
        self.agent_cost = []
        self.max_time = 0
        self.min_sum = 0
        for ag in range(self.num_agents):
            print('solving for ag', ag)
            self.solve_agent(ag)
            self.dijkstra_init(ag)
            self.agent_cost.append(0)


        for ag in range(self.num_agents):
            posY = self.agents_pos[ag][0]
            posX = self.agents_pos[ag][1]
            ag_sol = [(posX,posY)]

            t = 0
            while True:
                best_dir = self.best_dirs[ag][posY][posX]
                if len(best_dir) > 0:
                    best_dir = best_dir[0]
                else:
                    print(ag,posY,posX,best_dir)

                if best_dir == 'left':
                    posX -= 1
                elif best_dir == 'down':
                    posY -= 1
                elif best_dir == 'right':
                    posX += 1
                elif best_dir == 'up':
                    posY +=1
                elif best_dir == 'wait':
                    if self.max_time < t:
                        self.max_time = t
                    break

                self.total_cost += 1
                self.agent_cost[ag] += 1

                ag_sol.append((posX,posY))
                t+=1

            self.sol.append(ag_sol)

        self.min_sum = self.total_cost - self.max_time
        self.solved = True


    def write_to_lp_graph(self, outp):
        with open('{0}{1}.lp'.format(outp, ''), 'w') as out_file:
            print(os.path.abspath(out_file.name))
            #Write the time:
            #out_file.write('#const max_t = {0}.\n'.format(self.time))
            #out_file.write('time(1..max_t).\n\n')


            #write the map
            v_id = 0
            num_obs = 0
            map_ids = []
            for y in range(self.height):
                map_row = []
                for x in range(self.width):
                    extra = [0,0]
                    for ag in range(self.num_agents):
                        if self.agents_pos[ag][0] == y and self.agents_pos[ag][1] == x:
                            extra[0] = ag+1

                        if self.agents_pos[ag][2] == y and self.agents_pos[ag][3] == x:
                            extra[1] = ag+1

                    cell = self.map[y][x]
                    if cell != 1:
                        map_row.append(v_id)
                        v_id +=1
                    else:
                        map_row.append(-1)
                map_ids.append(map_row)

            out_file.write('nodes(0..{0}).\n'.format(v_id))


            for y in range(self.height):
                for x in range(self.width):
                    cell_id = map_ids[y][x]
                    if cell_id != -1:
                        if y + 1 < self.height and map_ids[y+1][x] != -1:
                            out_file.write('connected({0},{1}).\n'.format(cell_id, map_ids[y+1][x]))
                            out_file.write('connected({1},{0}).\n'.format(cell_id, map_ids[y+1][x]))
                        
                        if x + 1 < self.width and map_ids[y][x+1] != -1:
                            out_file.write('connected({0},{1}).\n'.format(cell_id, map_ids[y][x+1]))
                            out_file.write('connected({1},{0}).\n'.format(cell_id, map_ids[y][x+1]))
    


            #write the agents:
            out_file.write('%% Agents: \n')
            for ag in range(self.num_agents):
                out_file.write('robot({0}).\n'.format(ag))
            out_file.write('\n')

            
            out_file.write('%% Initial positions:: \n')
            for ag in range(self.num_agents):
                print(ag)
                v_id = map_ids[self.agents_pos[ag][0]][self.agents_pos[ag][1]]
                out_file.write('at({0},{1},0).\n'.format(ag, v_id))
            out_file.write('\n')
            



            #goal positions:
            out_file.write('%% Goal positions: \n')
            for ag in range(self.num_agents):
                v_id = map_ids[self.agents_pos[ag][0]][self.agents_pos[ag][1]]
                out_file.write('goal({0},{1}).\n'.format(ag, v_id))
            out_file.write('\n')



    def write_to_lp(self, outp):
        with open('{0}'.format(outp), 'w') as out_file:
            print(os.path.abspath(out_file.name))
            #Write the time:
            #out_file.write('#const bound = {0}.\n'.format(self.time))
            #out_file.write('time(1..bound).\n\n')

            #write the map
            out_file.write('rangeX(0..{0}).\n'.format(self.width-1))
            out_file.write('rangeY(0..{0}).\n\n'.format(self.height-1))

            
            out_file.write('%% Obstacles in map: \n')
            for obs in self.obstacles:
                out_file.write('obstacle({0},{1}).\n'.format(obs[1], obs[0]))
            out_file.write('\n')
            
            #goal positions:
            out_file.write('%% Goal positions: \n')
            for ag in range(self.num_agents):
                out_file.write('goal({0},{1},{2}).\n'.format(ag, self.agents_pos[ag][3], self.agents_pos[ag][2]))
            out_file.write('\n')


            #dijkstra values
            out_file.write('%% Dijkstra values: \n')            
            for ag in range(self.num_agents):
                h_val = self.heuristic[ag][self.agents_pos[ag][0]][self.agents_pos[ag][1]]
                out_file.write('dijkstra({0},{1}).\n'.format(ag, h_val))
            out_file.write('\n')


            #write the agents:
            out_file.write('%% Agents: \n')
            for ag in range(self.num_agents):
                out_file.write('robot({0}).\n'.format(ag))
            out_file.write('\n')

            
            
            out_file.write('%% Initial positions: \n')
            for ag in range(self.num_agents):
                out_file.write('at({0},{1},{2},0).\n'.format(ag, self.agents_pos[ag][1], self.agents_pos[ag][0]))
            out_file.write('\n')

            #min cost
            for ag in range(self.num_agents):
                print(ag)
                for y in range(self.height):
                    for x in range(self.width):
                        h1 = self.heuristic[ag][y][x]
                        #h2 = self.heuristic_initial[ag][y][x]
                        if h1 != -1:
                            out_file.write('cost_to_go({0},{1},{2},{3}).\n'.format(ag, x, y, h1))
                out_file.write('\n\n')
            
                
            

    def change_format(self, outp, num):
        with open('{0}{1}'.format(outp, ''), 'w') as out_file:
            out_file.write('{0}\n'.format(num))

            out_file.write('Grid:\n')
            out_file.write('{0},{1}\n'.format(self.height, self.width))
            for y in range(self.height):
                row = ''
                for x in range(self.width):
                    cell = self.map[y][x]
                    if self.map[y][x] == 1:
                        row += '@'
                    else:
                        row += '.'

                out_file.write('{0}\n'.format(row))

            out_file.write('Agents:\n')
            out_file.write('{0}\n'.format(self.num_agents))
            for ag in range(self.num_agents):
                aux_pos = (self.agents_pos[2], self.agents_pos[3], self.agents_pos[0], self.agents_pos[1])
 
                pos = ','.join(str(p) for p in self.agents_pos[ag])
                out_file.write('{0},{1}\n'.format(ag,pos))


    def read_sol(self, inp):
        self.ag_sol = []
        for ag in range(self.num_agents):
            self.ag_sol.append([])

        with open(inp, 'r') as in_file:
            preds = in_file.readline().split()
            for p in preds:
                if 'en' in p:
                    info=p.replace("on(","")
                    info=info.replace(")","")
                    tup = info.split(",")
                    tup = [int(tup[0][1:])-1,int(tup[1]),int(tup[2]),int(tup[3])]
                    self.ag_sol[tup[0]].append((tup[1],tup[2], tup[3]))

        for ag in range(self.num_agents):
            self.ag_sol[ag].sort(key=lambda tup: tup[2])
            print(self.ag_sol[ag])

        sol_cost = 0
        for ag in range(self.num_agents):
            #print(self.ag_sol[ag])
            final_pos = (self.agents_pos[ag][3], self.agents_pos[ag][2])
            for pos in self.ag_sol[ag]:
                if pos[0] == final_pos[0] and pos[1] == final_pos[1]:
                    break

                sol_cost += 1

        print(solv.sol_cost)

    def clingo_solve(self, inp):
        print('solving with clingo...')
        num = self.max_time
        ms0 = num
        while True:
            solv = asp_solver.IncrementalSolver(num, self.num_agents, self.min_sum, self.total_cost, ms0, True, True)            
            clingo.clingo_main(solv, [inp,'bases/baseE.lp','--opt-strat=usc,disjoint' ,'--outf=3' , '--time-limit=300', '-c','bound={0}'.format(num)])
            
            if solv.sol_cost > 0:
                self.sol = solv.resp
                self.check_makespan()
                print('Encontrada Primera Solucion') 
                print('\tCosto total: {0}'.format(solv.sol_cost))
                print('\tMakespan: {0}'.format(self.sol_time))
                
                ms = int(solv.theoric_makespan)
                if ms > num:
                    num = ms
                    solv = asp_solver.IncrementalSolver(num, self.num_agents, self.min_sum, self.total_cost, ms0, True, True)
                    clingo.clingo_main(solv, [inp, 'bases/baseE.lp','--opt-strat=usc,disjoint' ,'--outf=3' , '--time-limit=300', '-c','bound={0}'.format(ms)])
                break
            
            num += 1

        self.sol = solv.resp
        self.check_makespan()
        print('-----------------')
        print('Encontrada Solucion Optima, Estadisticas Clingo:')
        #print(json.dumps(solv.stats, sort_keys=True, indent=4, separators=(',', ': ')))
        print('Encontrada Solucion') 
        print('\tCosto total: {0}'.format(solv.sol_cost))
        print('\tMakespan: {0}'.format(self.sol_time))
        print('-----------------')
        

    def check_makespan(self):
        makespan = -1
        for ag in self.sol:
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

        #print(makespan)
        self.sol_time = makespan - 1

