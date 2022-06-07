from random import randint, choice
fsmForGenerate = [
    [('d',1), ('x',0), ('n',2), ('nd',0)],
    [('d',1), ('x',1), ('nd',1), ('n',2)],
    [('n',2), ('x',2), ('nd',2)]
]
	
def generate():
	s = ""
	i = 0
	v = choice(['a', 'e'])
	for _ in range(randint(4, 12)):
		n = choice(fsmForGenerate[i])
		s += v if n[0] == 'x' else n[0]
		i = n[1]
	return s

from sigmapie import *

m = MITSL(polar = "n")
m.data = [generate() for _ in range(256)]
m.extract_alphabet()
m.learn()

m.fsmize()

s460 = None