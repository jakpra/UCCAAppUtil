import sys
import json
import re

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
        
        context = re.sub('\\\\"', '"', _line[iContext])
        context = re.sub(' +', ' ', context)
        context = context.split()
        iTarget = context.index(f'|{token0}|')
        lcontext, target, rcontext = context[:iTarget], \
                                     context[iTarget:iTarget+len(token)], \
                                     context[iTarget+1:]#len(token):]

        assert [f'|{x}|' for x in token][0] == target[0], (token, token0, target, context)
          
        units.append((IDs[0], token0, _line[iScene], _line[iFunction], tuple(lcontext), tuple(rcontext), tuple(token)))

#print(json.dumps(units, indent=2))

all_tokens = []

for sent in sentences(corpus, format='conllu'):
    new_sent = True
    for tok in sent.tokens:
        tok.new_sent = new_sent
        tok.meta = sent.meta
        template = ['_'] *  9
        mo = re.match('.*(\d+\:\d+).*', tok.fields[-1])
        if mo:
            template[0] = mo.groups()[0]
        tok.fields = tok.fields[:-1] + template
        new_sent = False
        all_tokens.append(tok)


units = set(units)
total = len(units)
total_resolved = 0
discarded = set()

while units:
    unit_iterator = iter(sorted(units, key=itemgetter(0)))
    assert_fail_ctr = 0

    done_with_previous = True
    resolved_units = set()
    
    try:
        #for sent in sentences(corpus, format='conllu'):
        #   for k, tok in enumerate(sent.tokens):
        for k, tok in enumerate(all_tokens):
            lcont = tuple(t.word for t in all_tokens[max(0, k-10):k])
            rcont = tuple(t.word for t in all_tokens[k+1:min(k+11, len(all_tokens))])
            if done_with_previous:
                unit_candidate = next(unit_iterator)

                _id, unit_token0, scene, function, lcontext, rcontext, token = unit_candidate

            scene = scene.replace('Part/Portion', 'PartPortion')
            function = function.replace('Part/Portion', 'PartPortion')

            lcont = ''.join(lcont)
            rcont = ''.join(rcont)
            lcontext = ''.join(lcontext)
            rcontext = ''.join(rcontext)
            
     #           print(lcont)
     #           print(lcontext)
     #           print()
     #           print(rcont)
     #           print(rcontext)
     #           print()
     #           print()

            try:
                if scene in tabulate.depth1 or scene.startswith('`'):
                    pass
                else:
                    raise InvalidSS(scene)

                if function in tabulate.depth1 or function.startswith('`'):
                    pass
                else:
                    raise InvalidSS(function)

                min_l_len = min(10, len(lcontext))
                min_r_len = min(10, len(rcontext))
                
                #assert tok.word == unit_token0, (tok.word, unit_token0)
                assert lcont[-min_l_len:] == lcontext[-min_l_len:] and rcont[:min_r_len] == rcontext[:min_r_len], (lcont, lcontext, rcont, rcontext)

            except AssertionError as e:
                # print(e, file=sys.stderr)
                done_with_previous = False
                #pass

            except InvalidSS as e:
                print(e, file=sys.stderr)
                done_with_previous = True
                #pass

            else:
                resolved_units.add(unit_candidate)
                lexlemma = ' '.join(token).lower()
                lexlemma = re.sub('^his$', 'he', lexlemma)
                lexlemma = re.sub('^her$', 'she', lexlemma)
                tok.fields[12] = lexlemma
                tok.fields[13] = ('p.' if scene[0] != '`' else '') + scene
                tok.fields[14] = ('p.' if scene[0] != '`' else '') + function
                #            template[5] = unit_token0
                done_with_previous = True
                #            print('\t'.join(tok.fields[:-1] + template))

    #        if tok.word == "in" and "Buch" in rcont:
    #            print(tok.orig, lcont, lcontext, rcont, rcontext, sep='\n')
    #            exit(0)
    
#            if tok.new_sent:
#                print()
#                for line in tok.meta:
#                    print(line)
#            print('\t'.join(tok.fields[:-1] + template))

                #if tok.fields[-1].endswith('*'):
                #    while True:
                #        if done_with_previous:
                #            unit_candidate = next(unit_iterator)
                #        try:
                #            _id, unit_token0, scene, function, lcontext, rcontext = unit_candidate
                #            if scene in tabulate.depth1 and function in tabulate.depth1:
                #                assert tok.word == unit_token0, (tok.word, unit_candidate)
                #                #assert lcont == lcontext, (lcont, lcontext)
                #                #assert rcont == rcontext, (rcont, rcontext)
                #                #pass
                #            else:
                #                            raise InvalidSS
                #                pass
                #        except AssertionError as e:
                #            assert_fail_ctr += 1
                #            done_with_previous = False
                #            print(e, file=sys.stderr)
                #            #print('\t'.join(tok.fields + template))
                #            break
                #        except InvalidSS as e:
                #            done_with_previous = True
                #            continue
                #        else:
                #            template[3] = scene
                #            template[4] = function
                #            template[5] = unit_token0
                #            print('\t'.join(tok.fields[:-1] + template))
                #            done_with_previous = True
                #            break
                #        
                #else:
                #    print('\t'.join(tok.fields + template))
                #    #pass

    except StopIteration:
        if not resolved_units:
            # discarded += units
            print(f'{len(units)} units unresolved', file=sys.stderr)
            break
    #        raise Exception
        total_resolved += len(resolved_units)
        print(f'{total_resolved}/{total} units resolved', file=sys.stderr)
        units -= resolved_units

    else:
        if not resolved_units:
            units.remove(unit_candidate)
            discarded.add(unit_candidate)
            print(f'discarding... - {len(units)} units remaining', file=sys.stderr)
            
        total_resolved += len(resolved_units)
        print(f'{total_resolved}/{total} units resolved', file=sys.stderr)
        units -= resolved_units


with open('discarded.out', 'w') as f:
    for unit in sorted(discarded):
        print(unit, file=f)
        
# template = 9 * ['_']
for tok in all_tokens:
    if tok.new_sent:
#        break
         print()
         for line in tok.meta:
             print(line)
    print('\t'.join(tok.fields))

        
#print(assert_fail_ctr)
