import sys

from operator import itemgetter
from collections import defaultdict
from random import shuffle

from helpers import *

#infile = "/home/jakob/nert/UCCA-SNACS/data/the_little_prince/en/preprocessed/lpp.sents.en.full.marked.new"

infile = sys.argv[1] if len(sys.argv) > 1 else sys.stdin
format = sys.argv[2]
outfile = sys.argv[3]
maxsents = int(sys.argv[-1])

sentID2sent = {}
sentID2count = {}

lemmas = defaultdict(int)
all_units = 0


printed_sents = 0
# with open("passages/samples/balanced_lemmas.conllu", "w") as f:
with open(outfile, "w") as f:
    sents = list(sentences(infile, format=format))
    shuffle(sents)

    done = False
    while (not done) and printed_sents < maxsents:
        remaining = []
        for sent in sents:
            if len(sent.tokens) > 20:
                continue
            n_units = 0
            rare = 0
            frequent = 0
            for tok in sent.tokens:
                if tok.fields[-1].endswith("*") or (tok.format=="conllulex" and tok.ss and tok.ss.startswith("p.")):
                    n_units += 1
                    if lemmas.get(tok.lemma.lower(), 0) <= min(set(lemmas.values()).union({0})):
                        rare += 1
                    else:
                        frequent += 1
                    lemmas[tok.lemma.lower()] += 1

            if "many" not in sys.argv:
                if n_units >= 1 and rare >= (frequent * 1):
                    printed_sents += 1
                    all_units += n_units
                    for metaline in sent.meta:
                        f.write(metaline + "\n")
                    for token in sent.tokens:
                        f.write(token.orig + "\n")
                    f.write("\n")
                else:
                    remaining.append(sent)
            else:
                done = True

            sentID = sent.meta_dict["sent_id"]
            sentID2sent[sentID] = sent
            sentID2count[sentID] = n_units

            if printed_sents >= maxsents:
                break

        sents = remaining
        lemmas = defaultdict(int)


if "many" in sys.argv:
    with open(outfile, "w") as f:
        for sentID, count in list(sorted(sentID2count.items(), key=lambda x:x[1]/sentID2sent[x[0]].tokens, reverse=True))[:maxsents]:
            print("{}: {}".format(sentID, count), file=sys.stderr)
            sent = sentID2sent[sentID]
            for metaline in sent.meta:
                f.write(metaline + "\n")
            for token in sent.tokens:
                f.write(token.orig + "\n")
            f.write("\n")


