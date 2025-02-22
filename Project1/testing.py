from SearchAgent import SearchAgent
import time, sys, re
import numpy as np
import pandas as pd
from itertools import product as combine

# Getting test files
path = 'mazes/'
sizes = ['dense/','sparse/']
maze = ['1','2','3','4','5','6','7','8','9','10']
pos = ['a','b','c']
test_files = [path+s+i+l for (s,i,l) in list(combine(sizes,maze,pos))]

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + ' ' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)

def collect_data(data, out_path):
    # Gather info by grouping dense/sparse and map
    ids = data.groupby(['type','id'])
    ids_means = ids.mean()
    ids_means.name = 'ids_means'
    ids_max = ids.max().drop(columns='class')
    ids_max.name = 'ids_max'
    ids_min = ids.min().drop(columns='class')
    ids_min.name = 'ids_min'

    # Gather info by grouping dense/sparse
    types = data.groupby(['type'])
    types_means = types.mean()
    types_means.name = 'types_mean'
    types_max = types.max().drop(columns='class')
    types_max.name = 'types_max'
    types_min = types.min().drop(columns='class')
    types_min.name = 'types_min'

    dataframes = [data,ids_means,ids_max,ids_min,types_means,types_max,types_min,]
    if out_path:
        for df in dataframes: df.to_csv(f'{out_path}/{df.name}.csv')
                        
    return dataframes
    
#### TESTING ROUTINE ####

def run_tests(test_files, search, *args, repeat=1, out_path=''):
    print("#### Starting New Test Routine ####")
    keys = ['type','id','class',f'time_{repeat}avg',f'score_{repeat}avg',f'fails_{repeat}total','visited','repeated','explored']
    data = pd.DataFrame(columns=keys)
    data.name='all_data'
    count,total = 0, repeat*len(test_files)
    agent = None

    for maze_file in test_files: 
        maze = np.genfromtxt(maze_file, dtype=str, delimiter=1).astype('bytes')
        if not agent: agent = SearchAgent(maze) # Build agent if not yet created
        
        deltas = []
        fails = []
        costs = []
        visits = []
        repeated = []
        explored = []

        for i in range(1,repeat+1):
            count += 1
            progress(count, total, status=f"{maze_file} X{i:4d}")            
            
            # Set up new map
            agent.set_maze(maze)                # Reset agent's maze
            init,goal = agent.find_positions()  # Reset positions

            # Run and time it
            t0 = time.perf_counter()
            try:
                cost = search(agent, maze, init, goal, *args)
            except TimeoutError:
                cost = 0
            finally:
                tf = time.perf_counter()

            # Data acumulators
            deltas += [tf - t0]
            fails += [0 if cost else 1]
            costs += [0 if not cost else cost]
            visits += [agent.get_visited()]
            repeated += [agent.get_repeated()]
            explored += [agent.get_explored()]

        fails_ratio = sum(fails)/repeat
        deltas_avg = sum(deltas)/repeat # Consider failures
        if fails_ratio < 1:
            score_avg = sum(costs)/(repeat-sum(fails)) # Don't consider failures
        else:
            score_avg = 0
        visits_avg = sum(visits)/repeat
        repeated_avg = sum(repeated)/repeat
        explored_avg = sum(explored)/repeat

        # Fetch info from file name
        match = re.match(r'mazes/(\w+)/(\d+)(\w)', maze_file)
        maze_type = match.group(1)
        maze_id = int(match.group(2))
        maze_class = match.group(3)

        # Add results to dataframe
        values = [maze_type,maze_id,maze_class,deltas_avg,score_avg,
                  fails_ratio,visits_avg,repeated_avg,explored_avg]
        data.loc[maze_file] = dict(zip(keys, values))
    print("\n")

    # print(data)

    return collect_data(data, out_path)

#### SEARCH WRAPPERS FOR DIFFERENT METHODS ####
from SimulatedAnnealing import annealing
def simulated_annealing_pathcost(agent, maze, init, goal, *args):
    agent.formulate_problem(init, goal, False, [])
    agent.search(annealing, maze, goal, *args[0])
    return agent.get_solution()[1]

if __name__ == '__main__':
    for heu in ['pathcost']:
        run_tests(
                test_files, 
                simulated_annealing_pathcost, 
                [heu], 
                repeat=100, 
                out_path=f'data/annealing/{heu}'
                )
