#!/home/jakob/anaconda3/bin/python3.6

import sys

class Token:
    def __init__(self, string, format="conllu", conllulex=False):
        self.format = format
        self.fields = string.split("\t")
        self.orig = string
        self.checkmark = ""
        if format=="conllulex" or conllulex==True:
            self.conllulex()
        elif format=="conllu":
            self.conllu()
        elif format=="conll09":
            self.conll09()

    def conllu(self):
        self.offset, \
            self.word, \
            self.lemma, \
            self.ud_pos, \
            self.ptb_pos, \
            self.morph, \
            self.head, \
            self.deprel = [field if field.strip("_") else None for field in self.fields[:8]]

        self.default_pos = self.ptb_pos

    def conllulex(self):
        self.conllu()
        self.deps, \
            self.misc, \
            self.smwe, \
            self.lexcat, \
            self.lexlemma, \
            self.ss, \
            self.ss2, \
            self.wmwe, \
            self.wlemma, \
            self.wcat, \
            self.lextag = [field if field.strip("_") else None for field in self.fields[8:19]]

    def conll09(self):
        sent_offset, \
            self.word, \
            self.lemma, \
            _, \
            self.stts_pos, \
            _, \
            self.morph, \
            _, \
            self.head, \
            _, \
            self.deprel = [field if field.strip("_") else None for field in self.fields[:11]]

        self.default_pos = self.stts_pos
        self.sent_id, self.offset = sent_offset.split("_")

class Sentence:
    def __init__(self, tokens, meta):
        self.tokens = tokens
        self.meta = meta
        self.meta_dict = {}
        for meta_info in meta:
            try:
                k, v = meta_info.strip("# ").split("=", maxsplit=1)
                self.meta_dict[k.strip()] = v.strip()
            except ValueError:
                print("could not parse meta info: ", meta_info, ", at", meta[0], file=sys.stderr)

def sentences(filename, format="conllu", conllulex=False):
    tokens, meta = [], []
    f = open(filename) if type(filename) == str else filename
    for line in f:
        line = line.strip()
        if not line:
            yield Sentence(tokens, meta)
            tokens = []
            meta = []
        elif line.startswith("#"):
            meta.append(line)
        else:
            tokens.append(Token(line, format=format, conllulex=conllulex))
    f.close()

    if tokens:
        yield Sentence(tokens, meta)
        

def conllu(string):
    fields = string.split("\t")
    t = Token(string, fields)
    t.offset, \
        t.word, \
        t.lemma, \
        t.ud_pos, \
        t.ptb_pos, \
        t.morph, \
        t.head, \
        t.deprel = [field if field.strip("_") else None for field in fields[:8]]

    return t

def conllulex(string):
    t = conllu(string)
    t.deps, \
        t.misc, \
        t.smwe, \
        t.lexcat, \
        t.lexlemma, \
        t.ss, \
        t.ss2, \
        t.wmwe, \
        t.wlemma, \
        t.wcat, \
        t.lextag = [field if field.strip("_") else None for field in t.fields[8:19]]

    return t

def conll09(string):
    fields = string.split("\t")
    t = Token(string, fields)
    sent_offset, \
        t.word, \
        t.lemma, \
        _, \
        t.stts_pos, \
        _, \
        t.morph, \
        _, \
        t.head, \
        _, \
        t.deprel = [field if field.strip("_") else None for field in fields[:10]]

    t.sent_id, t.offset = sent_offset.split("_")
    
    return t
