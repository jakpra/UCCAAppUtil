import sys
import json

from operator import itemgetter

import tabulate
from helpers import *


if len(sys.argv) != 3:
    print(f'Usage: python {sys.argv[0]} <annotation.tsv> <corpus.conlluX>', file=sys.stderr)
    exit(1)

class InvalidSS(Exception):
    pass

    
anno = sys.argv[1]
corpus = sys.argv[2]


units = []

with open(anno) as f:
    first = True
    for line in f:
        _line = line.strip().split('\t')
        if first:
            headers = [x.lower() for x in _line]
            iScene = headers.index('adjudication') + 1  # index of scene role
            iFunction = iScene+1  # index of function
            iContext = headers.index('context') + 1
            first = False
        if not line.startswith('('):
            continue

        _id, _token = _line[0].rsplit(maxsplit=1)
        IDs = [int(x) for x in _id[1:-1].split(',') if x!='']
        token = _token.split('_')
        token0 = token[0]
        
        context = _line[iContext].split()
        iTarget = context.index(f'|{token0}|')
        lcontext, target, rcontext = context[:iTarget], \
                                     context[iTarget:iTarget+len(token)], \
                                     context[iTarget+len(token):]

        assert [f'|{x}|' for x in token] == target, (token, token0, target, context)
          
        units.append((IDs[0], token0, _line[iScene], _line[iFunction], lcontext, rcontext))

#print(json.dumps(units, indent=2))


unit_iterator = iter(sorted(units, key=itemgetter(0)))
assert_fail_ctr = 0

done_with_previous = True

try:
    for sent in sentences(corpus, format='conllu'):
        for tok in sent.tokens:
            template = ['_'] * 9
            if tok.fields[-1].endswith('*'):
                while True:
                    if done_with_previous:
                        unit_candidate = next(unit_iterator)
                    try:
                        _id, unit_token0, scene, function, lcontext, rcontext = unit_candidate
                        if scene in tabulate.depth1 and function in tabulate.depth1:
#                            assert tok.word == unit_token0, (tok.word, unit_candidate)
                            pass
                        else:
#                            raise InvalidSS
                            pass
                    except AssertionError as e:
                        assert_fail_ctr += 1
                        done_with_previous = False
                        #print('\t'.join(tok.fields + template))
                        break
                    except InvalidSS as e:
                        done_with_previous = True
                        continue
                    else:
                        template[3] = scene
                        template[4] = function
                        print('\t'.join([str(_id), unit_token0] + tok.fields[:-1] + template))
                        done_with_previous = True
                        break
                    
            else:
                #print('\t'.join(tok.fields + template))
                pass

except StopIteration:
    pass

print(assert_fail_ctr)
