import DFA.DFA as DFA
from IPython import embed
import dfa_grapher as dfg
from copy import deepcopy
import shutil
import os
# def merge(state1, state2, dfa):
#     '''
#     Merges state2 into state1 and removes state2
#     '''
#     transitions = dfa.transitions
#     for s in dfa.states:
#         if s in transitions:
#             for token in transitions[s]:
#                 if state2 in transitions[s][token]:
#                     transitions[s][token] = state1
#         if state2 in transitions:
#             for token in transitions[state2]:
#                 if s in transitions[state2][token]:
#                     transitions[state1][token] = s
#     if dfa.start == state2:
#         dfa.start = state1
#     if state2 in dfa.accepts:
#         dfa.accepts = dfa.accepts.difference({state2}).union({state1})
#     if state2 in transitions:
#         del transitions[state2]
#     dfa.states.remove(state2)
#     dfa.transitions = transitions
#     return dfa


def choose(dfa, states):
    '''
    Choose first from a set of states in standard order
    '''
    for state in get_state_order(dfa):
        if state in states:
            return state


def learn_dfa(teacher, num_examples):

    for i in range(num_examples):
        teacher.example()
    examples = teacher.used_examples
    pos_examples = [ex[0] for ex in examples if ex[1] == '+']
    neg_examples = [ex[0] for ex in examples if ex[1] == '-']
    pta = DFA.from_word_list(pos_examples, alphabet)
    return pta


def rpni_compatible(dfa, neg_examples):
    for neg_ex in neg_examples:
        if dfa.recognizes(neg_ex):
            return False
    return True


def get_counterexample(dfa, neg_examples):
    for neg_ex in neg_examples:
        if dfa.recognizes(neg_ex):
            return neg_ex
    return None


def get_state_order(dfa):
    bla = dfa.copy()
    levels = bla.levels()

    levelsDict = {}

    levels.pop('sink', None)

    for key in levels:
        if not levels[key] in levelsDict:
            levelsDict[levels[key]] = [key]
        else:
            levelsDict[levels[key]].append(key)
        levelsDict[levels[key]].sort()

    output = []
    for level in sorted(levelsDict):
        for value in levelsDict[level]:
            output.append(value)
    print(output)
    return output


class Learner:
    def __init__(self):
        self.alphabet = ['a', 'b']
        self.reds = None
        self.blues = None
        self.draw_counter = 0

    def draw(self, dfa, filepath='rpni/rpni', operation=''):
        dfg.draw_dfa_colored(dfa, self.reds, self.blues, '{}_{}_{}.png'.format(
            filepath, self.draw_counter, operation))
        self.draw_counter += 1

    def rpni_promote(self, dfa, state):
        self.reds.add(state)
        if state in self.blues:
            self.blues.remove(state)
        for token, state in dfa.transitions[state].items():
            self.blues.add(state)
        return dfa

    def rpni_fold(self, dfa, red_state, blue_state):
        '''folds blue_state into red_state'''
        print('Folding red:{} and blue:{}'.format(
            red_state, blue_state))

        transitions = dfa.transitions
        if blue_state in dfa.accepts:
            dfa.accepts.add(red_state)
            dfa.accepts.remove(blue_state)
        for token in self.alphabet:
            # print(token, transitions[blue_state], self.alphabet)
            if blue_state in transitions and token in transitions[blue_state]:
                if token in transitions[red_state]:
                    dfa = self.rpni_fold(
                        dfa, transitions[red_state][token], transitions[blue_state][token])
                else:
                    transitions[red_state][token] = transitions[blue_state][token]
                    del transitions[blue_state][token]
                    dfa.states.remove(blue_state)
                    dfa.transitions = transitions
                    self.draw(dfa=dfa, operation='fold')

        dfa.transitions = transitions
        return dfa

    def rpni_merge(self, dfa, red_state, blue_state):
        print('Merging red:{} and blue:{}'.format(
            red_state, blue_state))
        for state, state_trans in dfa.transitions.items():
            for token, next_state in state_trans.items():
                if next_state == blue_state:
                    dfa.transitions[state][token] = red_state
        # self.draw(dfa=dfa, operation='merge')
        return self.rpni_fold(dfa, red_state, blue_state)

    def rpni(self, pos_examples, neg_examples):
        dfa = DFA.from_word_list(pos_examples, self.alphabet)
        self.reds = {dfa.start}
        self.blues = {next_state for token,
                      next_state in dfa.transitions[dfa.start].items()}
        self.draw(dfa=dfa, operation='pta')
        while self.blues:
            blue = choose(dfa, self.blues)
            for red in list(self.reds):
                temp_dfa = self.rpni_merge(deepcopy(dfa), red, blue)
                if rpni_compatible(temp_dfa, neg_examples):
                    print('compatible')
                    # embed()
                    if blue in self.blues:
                        self.blues.remove(blue)
                    dfa = temp_dfa
                    for r_state in self.reds:
                        for token, next_state in dfa.transitions[r_state].items():
                            if next_state not in self.reds:
                                self.blues.add(next_state)
                    self.draw(dfa=dfa, operation='merge')
                else:
                    self.draw(dfa=temp_dfa, operation='counterex_{}'.format(
                        get_counterexample(temp_dfa, neg_examples)))
                    self.rpni_promote(dfa, blue)
                    self.draw(dfa=dfa, operation='promoted')

        return dfa


if __name__ == '__main__':
    dir = "rpni"
    if os.path.exists(dir):
        shutil.rmtree(dir, ignore_errors=True)
    os.makedirs(dir)

    l = Learner()
    l.rpni(['aaa', 'aaba', 'bba', 'bbaba'], ['a', 'bb', 'aab', 'aba'])
