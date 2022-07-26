from sigmapie import *
import pickle
import os

def get(experiment, data):
	return pickle.load(open(f'results_/mitsl{experiment}/{data}', 'rb'))
    
def tier(grammar, restrictions):
    return {tier for tier, restriction in grammar.grammar.items() if any(r in restrictions for r in restriction)}
    
class c:
    def __repr__(self):
        os.system('cls')
        return '\r'
clear = c()