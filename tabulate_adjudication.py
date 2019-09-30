import sys

adj_filename = sys.argv[1]
master_filename = sys.argv[2]


items = []
issues = []
context = ''
target = ''
adj1 = ''
adj2 = ''
with open(adj_filename) as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        if not line.strip():
            if context and target:
                # if adj1 != '?' and adj2 != '?':
                items.append((target, adj1, adj2, context))
                # else:
                #     issues.append((target, adj1, adj2, context))
            # else:
            #    print(f'target and/or context empty: {target}, {context}', file=sys.stderr)
            context = target = adj1 = adj2 = ''
            continue

        _line = line.split('\t')
        line_0 = _line[0]
        if line_0.startswith('Annotator '):
            pass
        elif line_0 == 'Your Decision':
            adj1, adj2 = _line[2:4]
        elif not line_0 and '|' in line:
            l, tgt, _, r = _line[1:5]
            context = f'{l} {tgt} {r}'.strip()
            target = '_'.join([t.strip('|') for t in tgt.split() if t.startswith('|') and t.endswith('|')])
        else:
            raise Exception(f'unexpected line ({i}): {line}')

master_items = []
token_ids = []
context = ''
with open(master_filename) as f:
    for i, line in enumerate(f):
        if not line.strip():
            if context and token_ids:
                master_items.append((tuple(token_ids), context))
            # else:
            #     print(f'token_ids and/or context empty: {token_ids}, {context}', file=sys.stderr)
            context = ''
            token_ids = []
            continue

        _line = line.split('\t')
        line_0 = _line[0]
        if line_0.startswith('# token_ids'):
            ids = line_0.split('=')[1].strip().split()
            token_ids = list(map(int, ids))
        elif line_0.startswith('# task_ids'):
            pass
        elif not line_0 and '|' in line:
            l, tgt, _, r = _line[1:5]
            context = f'{l} {tgt} {r}'.strip()
#        else:
#            raise Exception(f'unexpected line ({i}): {line}')

print('', 'Adjudication', '', 'context', sep='\t')
for it, mit in zip(items, master_items):
    target, adj1, adj2, context = it
    token_ids, mcontext = mit
    assert context == mcontext, (token_ids, target, context, mcontext)
    if adj1 != '?' and adj2 != '?':
        print(f'{token_ids} {target}', adj1, adj2, context, sep='\t')
