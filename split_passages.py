import sys

filename = sys.argv[1]
try:
    token_threshold = int(sys.argv[2])
    delim = None
except ValueError:
    token_threshold = None
    delim = sys.argv[2]
    
sep_files = "-f" in sys.argv


token_buffer_counter = 0
token_buffer = []
passage_counter = 0

with open(filename) as f:
    for line in f:
        line = line.strip()

        if delim == None or line != delim:
            token_buffer.append(line)
            token_buffer_counter += len(line.split())

        if (token_threshold != None and token_buffer_counter >= token_threshold) or line == delim:
            passage_counter += 1
            
            if sep_files:
                with open(filename + "." + str(passage_counter), "w") as g:
                    for ln in token_buffer:
                        g.write(ln + "\n")
            else:
                for ln in token_buffer:
                    print(ln)
                print("\n<DELIMITER>\n")
            token_buffer = []
            token_buffer_counter = 0

    if token_buffer:
        passage_counter += 1
        if sep_files:
            with open(filename + "." + str(passage_counter), "w") as g:
                for ln in token_buffer:
                    g.write(ln + "\n")
        else:
            for ln in token_buffer:
                print(ln)
