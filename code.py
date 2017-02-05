class Op(object):
    def __init__(self, ins, ip, kind, data):
        self.ins = ins
        self.ip = ip
        self.kind = kind
        # for dp or *dp affecting ops, this is how much to change
        # for jmps this is target ip
        self.data = data
    
    def __repr__(self):
        return "Op('{}', {}, {}, {})".format(self.ins,
                                             self.ip,
                                             self.kind,
                                             self.data)

def parse_code_string(code):
    """
    Parse a piece of Brainfuck code, returning a list of Ops
    """
    ops = []
    stack = [] # stack of open-brackets.
    curr_ip = 0
    for ins in code:
        if ins   == '>':
            op = Op(ins, curr_ip, 'MovDp', 1)
        elif ins == '<':
            op = Op(ins, curr_ip, 'MovDp', -1)
        elif ins == '+':
            op = Op(ins, curr_ip, 'ChangeDp', 1)
        elif ins == '-':
            op = Op(ins, curr_ip, 'ChangeDp', -1)
        elif ins == '.':
            op = Op(ins, curr_ip, 'Output', None)
        elif ins == ',':
            op = Op(ins, curr_ip, 'Input', None)
        elif ins == '[':
            op = Op(ins, curr_ip, 'JEZ', None)
            stack.append(op)
        elif ins == ']':
            match = stack.pop()
            op = Op(ins, curr_ip, 'JNZ', match.ip+1)
            match.data = curr_ip+1
        curr_ip += 1
        ops.append(op)
    assert stack == []
    return ops

if __name__ == '__main__':
    ops = parse_code_string('[->+<]') # add 2 nums
    for op in ops:
        print op
