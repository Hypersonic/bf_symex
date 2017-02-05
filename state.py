import z3
from copy import copy

from code import parse_code_string


MEM_SIZE = 16

class TerminatedState(Exception):
    """
    Exception to say that a program has finished running.
    """
    pass


class State(object):
    def __init__(self, ip, dp, code, memory, path, input_data, output_data):
        self.ip = ip
        self.dp = dp
        self.code = code
        self.memory = memory
        self.path = path
        self.input_data = input_data
        self.output_data = output_data
        self.sat = False
        self.model = None

    def clone(self, no_copy=False):
        if no_copy:
            memory = self.memory
        else:
            memory = copy(self.memory)

        def simplify(x):
            try:
                return z3.simplify(x)
            except z3.Z3Exception:
                return x

        memory = map(simplify, memory) # simplify expressions for memory stuffs

        return State(ip = self.ip, \
                     dp = self.dp, \
                     code = self.code, \
                     memory = memory, \
                     path = copy(self.path), \
                     input_data = self.input_data, \
                     output_data = copy(self.output_data))


    def get_successor_states(self):
        if 0 <= self.ip < len(self.code):
            op = self.code[self.ip]
        else:
            raise TerminatedState()
        if op.kind == 'MovDp':
            new_dp = self.dp + op.data
            st = self.clone(no_copy = True)
            st.ip = self.ip + 1
            st.dp = new_dp
            return [st]
        elif op.kind == 'ChangeDp':
            st = self.clone()
            st.memory[st.dp] += op.data
            st.ip = self.ip + 1
            return [st]
        elif op.kind == 'Output':
            st = self.clone(no_copy = True)
            out = st.memory[st.dp]
            st.ip = self.ip + 1
            #print 'OUT:::', out
            st.output_data.append(out)
            return [st]
        elif op.kind == 'Input':
            inp = z3.Int('inp_{}'.format(len(self.input_data)))
            st = self.clone()
            st.ip = self.ip + 1
            st.memory[st.dp] = inp
            st.input_data.append(inp)
            return [st]
        elif op.kind == 'JEZ':
            taken = self.clone(no_copy = True) # branch where we jump
            not_taken = self.clone(no_copy = True) # branch where we don't jump
            # add the path predicates
            taken.path.append(taken.memory[taken.dp] == 0)
            not_taken.path.append(not_taken.memory[not_taken.dp] != 0)
            # ip changes
            taken.ip = op.data
            not_taken.ip = self.ip + 1
            return [taken, not_taken]
        elif op.kind == 'JNZ':
            taken = self.clone(no_copy = True) # branch where we jump
            not_taken = self.clone(no_copy = True) # branch where we don't jump
            # add the path predicates
            taken.path.append(taken.memory[taken.dp] != 0)
            not_taken.path.append(not_taken.memory[not_taken.dp] == 0)
            # ip changes
            taken.ip = op.data
            not_taken.ip = self.ip + 1
            return [taken, not_taken]
        else:
            raise NotImplementedError('Op not implemented: {}'.format(op))

    def concretize(self):
        solver = z3.Solver()
        predicate = z3.And(*self.path)
        predicate = z3.simplify(predicate)
        solver.add(predicate)

        if solver.check() != z3.sat:
            self.sat = False
            return

        self.sat = True
        self.model = solver.model()

        return self.sat



    def __repr__(self):
        return 'State({ip}, {dp})'.format(ip = self.ip,
                                          dp = self.dp)

    @classmethod
    def create_entry_state(cls, code):
        memory = [0 for _ in range(MEM_SIZE)] # memory is just constant 0's untiul symbolic data is introduced
        code = parse_code_string(code)
        return cls(ip = 0,
                   dp = 0,
                   code = code,
                   memory = memory,
                   path = [],
                   output_data = [],
                   input_data = [])



class PathGroup(object):
    def __init__(self, live, dead):
        self.live = live
        self.dead = dead
        self.goals = set() # just a way to collect all the goal states we've found

    def explore_until_ip(self, ip):
        return self.explore_until_fn(lambda st: st.ip == ip)

    def explore_until_fn(self, goal_fn):
        while self.live:
            st = self.live.pop()
            if goal_fn(st): # check against goal fn, if it matches move this to goals and return it
                self.goals.add(st)
                return st
            try:
                succs = st.get_successor_states()
                self.live.update(set(succs))
            except TerminatedState:
                dead.add(st)
            print "{} live, {} dead, {} goal".format(len(self.live),
                                                     len(self.dead),
                                                     len(self.goals))

if __name__ == '__main__':
    program = ',>,[<+>-]<.'
    entry_state = State.create_entry_state(program)
    live = {entry_state}
    dead = set()
    pg = PathGroup(live, dead)
    def goal_fn(st):
        if st.ip != len(program):
            return False
        st.path.append(st.input_data[0] == 14)
        st.path.append(st.output_data[0] == 24)
        if not st.concretize():
            return False
        return True
    pg.explore_until_fn(goal_fn = goal_fn)
    print pg.goals
    for st in pg.goals:
        print 'MODEL:', st.model
