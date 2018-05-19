import sys

from helpers import *


corpus = sys.argv[1]
idsFile = sys.argv[2]
invert = "-v" in sys.argv

ids = set()

with open(idsFile) as f:
    for line in f:
        ids.add(line.strip())


def invertIfFlag(boolean, flag):
    return boolean if not flag else not boolean


i = 0
for sent in sentences(corpus, format="conllulex"):
    sent_id = sent.meta_dict["streusle_sent_id"]
    if invertIfFlag(sent_id in ids, invert):
        i += 1
        ids.remove(sent_id)
        
        for meta_line in sent.meta:
            print(meta_line)
        for tok in sent.tokens:
            print(tok.orig)

        print()

print("found {} sentences".format(i), file=sys.stderr)
for sid in ids:
    print("didn't find {}".format(sid), file = sys.stderr)
