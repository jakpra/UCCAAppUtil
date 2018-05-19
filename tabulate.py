import sys
import json

from collections import defaultdict
from operator import itemgetter

def ID2item(x_key, task):
    d = {}
    for item in task[x_key]:
        d[item["id"]] = item
    return d

def isCompleted(task, required=[54]):
    for unit in task["annotation_units"]:
        needs_refinement = False
        has_refinement = False
        for cat in unit["categories"]:
            if cat["slot"] > 2:
                if cat["id"] in required:
                    needs_refinement = True
            else:
                has_refinement = True
                break
        if not needs_refinement or has_refinement:
            continue
        else:
            return False
    return True

def getContext(_tokIDs, tokId2tok, window=10):
    tokIDs = list(sorted(_tokIDs))
    first = tokIDs[0]
    last = tokIDs[-1]
    return [tokId2tok.get(ID, {}).get("text", "").replace("\n", " ") for ID in range(first-window, first)], [tokId2tok.get(ID, {}).get("text", "").replace("\n", " ") for ID in range(last+1, last+window+1)]


hierarchy = {"Circumstance": {"Temporal" : {"Time" : {"StartTime", "EndTime"}, "Frequency":{}, "Duration":{}, "Interval":{}}, "Locus" : {"Source", "Goal"}, "Path" : {"Direction", "Extent"}, "Means":{}, "Manner":{}, "Explanation" : {"Purpose"}},
             "Participant" : {"Causer": {"Agent" : {"Co-Agent"}}, "Theme" : {"Co-Theme", "Topic"}, "Stimulus":{}, "Experiencer":{}, "Originator":{}, "Recipient":{}, "Cost":{}, "Beneficiary":{}, "Instrument":{}},
             "Configuration" : {"Identity":{}, "Species":{}, "Gestalt" : {"Possessor", "Whole"}, "Characteristic" : {"Possession":{}, "Part/Portion" : {"Stuff"}}, "Accompanier":{}, "InsteadOf":{}, "ComparisonRef":{}, "RateUnit":{}, "Quantity" : {"Approximator"}, "SocialRel" : {"OrgRole"}}
}

depth1, depth2, depth3 = defaultdict(str), defaultdict(str), defaultdict(str)

for k1, v1 in hierarchy.items():
    depth1[k1] = k1
    depth2[k1] = k1
    depth3[k1] = k1
    for k2, v2 in v1.items():
        depth1[k2] = k1
        depth2[k2] = k2
        depth3[k2] = k2
        for k3 in v2:
            depth1[k3] = k1
            depth2[k3] = k2
            depth3[k3] = k3
            if type(v2) == dict:
                v3 = v2[k3]
                for k4 in v3:
                    depth1[k4] = k1
                    depth2[k4] = k2
                    depth3[k4] = k3

def coarsen(tag, depth=None):
    if depth == 1:
        return depth1[tag]
    elif depth == 2:
        return depth2[tag]
    elif depth == 3:
        return depth3[tag]
    else:
        return tag

def consider(tokenIDs, token_annotations, users, exclude=False):
    if not exclude: return True
    skip = False
    for user in users:
        cats = token_annotations.get(user, ({1: ""}, ""))[0].values()
        if not cats or any((not cat or "?" in cat or "`" in cat) for cat in cats):
            print(tokenIDs, token_annotations, file=sys.stderr)
            return False
    return True
        
def main(args):
    filename = args[0]

    with open(filename) as f:
        tasks = json.load(f)

    relevant_units = defaultdict(dict)
    all_users = set()

    first_task = list(tasks.values())[0]
    
    catId2cat = ID2item("categories", first_task["project"]["layer"])
    tokId2tok = ID2item("tokens", first_task)
    
    for taskID, task in tasks.items():
        userfname = task["user"]["first_name"]
#        if not isCompleted(task):
#            print("WARNING: task {} ({}) is not completed and will be ignored".format(taskID, userfname), file=sys.stderr)
#            continue
        
        all_users.add(userfname)
            
        
        #    catId2cat = ID2item("categories", task)
        #    tokId2tok = ID2item("tokens", task)
        #    unitId2unit = ID2item("annotation_units", task)
        
        for unit in task["annotation_units"]:            
            tokenIDs = tuple(tok["id"] for tok in unit["children_tokens"])                
            refinement = {cat["slot"]: catId2cat[cat["id"]]["name"] for cat in unit["categories"] if cat["slot"] <= 2}
            if refinement or unit["comment"]:
                try:
                    tokId2tok[tokenIDs[0]]
                except KeyError:
                    tokId2tok.update(ID2item("tokens", task))
                
                relevant_units[tuple(sorted(tokenIDs))][userfname] = (refinement, unit["comment"].replace("\n", " "))

    all_users = sorted(all_users)

    considered_units = {}
    for tokenIDs, users in relevant_units.items():
        # skip = False
        # for user in all_users:
        #     cats = users.get(user, ({1: ""}, ""))[0].values()
        #     if not cats or any((not cat or "?" in cat or "`" in cat) for cat in cats):
        #         skip = True
        #         print(tokenIDs, users, file=sys.stderr)
        #         break
        if consider(tokenIDs, users, all_users, exclude=("excl" in args)):
            considered_units[tokenIDs] = users

    
    if "lex" in args:

        ## All units
        print("\t" + "\t\t\t\t".join(all_users) + "\t\t\t\t" + "\t\t".join(["plurality vote", "majority vote", "adjudication"]) + "\t" + "\t".join(["comments", "agreement", "context"]))
        print("\t" + "\t".join(len(all_users) * ["scene", "", "function", ""]) + "\t".join(3 * ["scene", "function"]))

        _considered_units = considered_units.items()
        for tokenIDs, users in _considered_units:
            
            tokens = "_".join([tokId2tok[ID]["text"] for ID in sorted(tokenIDs)])
            line = "{} {}".format(tokenIDs, tokens)
            uniq_scene = defaultdict(int)
            uniq_func = defaultdict(int)

            maj_vote = {}
            plur_vote = {}

            comments = ""
            for user in all_users:
                cats, comment = users.get(user, ({}, ""))
                scene = cats.get(1, "")
                func = cats.get(2, scene)
                uniq_scene[scene] += 1
                uniq_func[func] += 1
                
                user_cats = "{}\t\t{}\t".format(scene, func) #, comment)
                line += "\t{}".format(user_cats)

                if comment:
                    comments += "{}: {}; ".format(user, comment)


            scene_agree, func_agree = sorted(uniq_scene.items(), key=itemgetter(1), reverse=True), sorted(uniq_func.items(), key=itemgetter(1), reverse=True)
            scene_argmax_agree, scene_max_agree = scene_agree[0] #/len(all_users) # 1 / len(uniq_scene.keys()) # max(uniq_scene.values())/4
            func_argmax_agree, func_max_agree = func_agree[0] #/len(all_users) # 1 / len(uniq_func.keys()) # max(uniq_func.values())/4 if uniq_func else None
            if len(scene_agree) > 1 and scene_agree[1][1] == scene_max_agree:
                scene_argmax_agree = ""
            if len(func_agree) > 1 and func_agree[1][1] == func_max_agree:
                func_argmax_agree = ""

            plur_vote[1] = scene_argmax_agree
            plur_vote[2] = func_argmax_agree
            if scene_max_agree/len(all_users) > .5:
                maj_vote[1] = scene_argmax_agree
            else:
                maj_vote[1] = ""
                
            if func_max_agree/len(all_users) > .5:
                maj_vote[2] = func_argmax_agree
            else:
                maj_vote[2] = ""
                
            if tokenIDs in considered_units:
                considered_units[tokenIDs]["_plurality_"] = (plur_vote, "")
                considered_units[tokenIDs]["_majority_"] = (maj_vote, "")
            
            line += "\t{}\t{}\t{}\t{}\t\t\t".format(scene_argmax_agree, func_argmax_agree, maj_vote[1], maj_vote[2]) + comments
            line += "\t" + str(scene_max_agree/len(all_users)) + "\t" + str(func_max_agree/len(all_users))
            left, right = getContext(tokenIDs, tokId2tok, window=20)
            line += "\t" + " ".join(left) + " " + " ".join(["|{}|".format(tokId2tok[ID]["text"]) for ID in tokenIDs]) + " " + " ".join(right)
            print(line.replace('"', '\\"'))

    if "conf" in args:
        # print("\taccuracy\tcohen's kappa")


        count1 = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))) #, "function":{"_all_": defaultdict(lambda: defaultdict(int))}, "exact":{}}
        count2 = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))) # {"scene":{"_all_": defaultdict(lambda: defaultdict(int))}, "function":{"_all_": defaultdict(lambda: defaultdict(int))}, "exact":{}}
        count3 = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))) # {"scene":{"_all_": defaultdict(lambda: defaultdict(int))}, "function":{"_all_": defaultdict(lambda: defaultdict(int))}, "exact":{}}
        count = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))) # {"scene":{"_all_": defaultdict(lambda: defaultdict(int))}, "function":{"_all_": defaultdict(lambda: defaultdict(int))}, "exact":{}}

        fleiss = {"scene":{}, "function":{}, "exact":{}}
        cohen = {"scene":{}, "function":{}, "exact":{}}

        agree1 = {"scene":defaultdict(int), "function":defaultdict(int), "exact":defaultdict(int)}
        agree2 = {"scene":defaultdict(int), "function":defaultdict(int), "exact":defaultdict(int)}
        agree3 = {"scene":defaultdict(int), "function":defaultdict(int), "exact":defaultdict(int)}
        agree = {"scene":defaultdict(int), "function":defaultdict(int), "exact":defaultdict(int)}
        
        acc1 = {"scene":{}, "function":{}, "exact":{}}
        acc2 = {"scene":{}, "function":{}, "exact":{}}
        acc3 = {"scene":{}, "function":{}, "exact":{}}
        acc = {"scene":{}, "function":{}, "exact":{}}
        dimensions= set() # {"scene":set(), "function":set(), "exact":set()}
        for user1 in all_users + ["_plurality_", "_majority_"]:
            for user2 in all_users + ["_plurality_", "_majority_"]:
                pair = "|".join((user1, user2))
                inverse_pair = "|".join((user2, user1))
                if user1 != user2 and inverse_pair not in count["exact"]:
                    count["scene"][pair] = defaultdict(lambda: defaultdict(int))
                    count["function"][pair] = defaultdict(lambda: defaultdict(int))
                    count["exact"][pair] = defaultdict(lambda: defaultdict(int))
                    # agree["scene"][pair] = defaultdict(int)
                    # agree["function"][pair] = defaultdict(int)
                    # agree["exact"][pair] = defaultdict(int)
                    n_units = 0
                    n_considered_units = 0
                    for tokenIDs, users in considered_units.items():
                        n_units += 1

                        n_considered_units += 1
                        
                        cats1, _ = users.get(user1, ({}, ""))
                        scene1 = cats1.get(1, "")
                        func1 = cats1.get(2, scene1)

                        cats2, _ = users.get(user2, ({}, ""))
                        scene2 = cats2.get(1, "")
                        func2 = cats2.get(2, scene2)

                        dimensions.add(scene1)
                        dimensions.add(scene2)
                        dimensions.add(func1)
                        dimensions.add(func2)

                        s1 = bool(scene1.strip("?") and "`" not in scene1)
                        s2 = bool(scene2.strip("?") and "`" not in scene2)
                        s1s2 = s1 and s2
                        # if True: #s1s2:
                        count["scene"][pair][scene1][scene2] += 1
                        count["scene"][pair][scene1]["_total_"] += 1
                        count["scene"][pair]["_total_"][scene2] += 1
                        count["scene"][pair]["_total_"]["_total_"] += 1

                        if "_majority_" not in pair and "_plurality_" not in pair:    
                            count["scene"]["_all_"][scene1][scene2] += 1
                            count["scene"]["_all_"][scene1]["_total_"] += 1
                            count["scene"]["_all_"]["_total_"][scene2] += 1
                            if scene1 != scene2:
                                count["scene"]["_all_"][scene2][scene1] += 1
                                count["scene"]["_all_"][scene2]["_total_"] += 1
                                count["scene"]["_all_"]["_total_"][scene1] += 1
                                count["scene"]["_all_"]["_total_"]["_total_"] += 2
                            else:
                                count["scene"]["_all_"]["_total_"]["_total_"] += 1
                        if scene1 == scene2:
                            agree["scene"][pair] += 1
                        if depth1[scene1] == depth1[scene2]:
                            agree1["scene"][pair] += 1
                        if depth2[scene1] == depth2[scene2]:
                            agree2["scene"][pair] += 1
                        if depth3[scene1] == depth3[scene2]:
                            agree3["scene"][pair] += 1

                        f1 = bool(func1.strip("?") and "`" not in func1)
                        f2 = bool(func2.strip("?") and "`" not in func2)
                        f1f2 = f1 and f2
                        # if True: #f1f2:
                        count["function"][pair][func1][func2] += 1
                        count["function"][pair][func1]["_total_"] += 1
                        count["function"][pair]["_total_"][func2] += 1
                        count["function"][pair]["_total_"]["_total_"] += 1

                        if "_majority_" not in pair and "_plurality_" not in pair:
                            count["function"]["_all_"][func1][func2] += 1
                            count["function"]["_all_"][func1]["_total_"] += 1
                            count["function"]["_all_"]["_total_"][func2] += 1
                            if func1 != func2:
                                count["function"]["_all_"][func2][func1] += 1
                                count["function"]["_all_"][func2]["_total_"] += 1
                                count["function"]["_all_"]["_total_"][func1] += 1
                                count["function"]["_all_"]["_total_"]["_total_"] += 2
                            else:
                                count["function"]["_all_"]["_total_"]["_total_"] += 1
                        if func1 == func2:
                            agree["function"][pair] += 1
                        if depth1[func1] == depth1[func2]:
                            agree1["function"][pair] += 1
                        if depth2[func1] == depth2[func2]:
                            agree2["function"][pair] += 1
                        if depth3[func1] == depth3[func2]:
                            agree3["function"][pair] += 1
                                
                        if s1s2 and f1f2:
                            exact1 = "|".join((scene1, func1))
                            exact2 = "|".join((scene2, func2))
                            count["exact"][pair][exact1][exact2] += 1
                            count["exact"][pair][exact1]["_total_"] += 1
                            count["exact"][pair]["_total_"][exact2] += 1
                            count["exact"][pair]["_total_"]["_total_"] += 1
                            if exact1 == exact2:
                                agree["exact"][pair] += 1


    #        dimensions.remove("?")
    #        dimensions.remove("_total_")
        dimensions = list(sorted(dimensions))
        dimensions = ["Circumstance", #"Temporal",
                      "Time", "StartTime", "EndTime", "Frequency", "Duration", #"Interval",
                      "Locus", "Source", "Goal", "Path", "Direction", "Extent", "Means", "Manner", "Explanation", "Purpose", #"Participant",
                      "Causer", "Agent","Co-Agent", "Theme", #"Co-Theme",
                      "Topic", "Stimulus", "Experiencer", "Originator", "Recipient", #"Cost",
                      "Beneficiary", "Instrument", #"Configuration",
                      "Identity", #"Species",
                      "Gestalt", "Possessor", "Whole", "Characteristic", "Possession", "Part/Portion", "Stuff", "Accompanier", #"InsteadOf",
                      "ComparisonRef", #"RateUnit",
                      "Quantity", #"Approximator",
                      "SocialRel", "OrgRole"]
#        dimensions.append("_total_")
        
        print("\t" + "\t".join(dimensions))

        ## Accuracy and Kappa
        for _scope in ["exact", "scene", "function"]:
            print((len(_scope) + 4) * "#")
            print("# {} #".format(len(_scope)*" "))
            print("# {} #".format(_scope))
            print("# {} #".format(len(_scope)*" "))
            print((len(_scope) + 4) * "#")
            print()
            print("\taccuracy\t\td3\t\td2\t\td1\t\tcohen's kappa\n")
            scope = count[_scope]
            pairs = sorted(pair for pair in scope.keys() if "_" not in pair)
            majority = sorted(pair for pair in scope.keys() if "_majority_" in pair)
            plurality = sorted(pair for pair in scope.keys() if "_plurality_" in pair)
            for pair in list(pairs) + list(plurality) + list(majority):
                if pair == "_all_":
                    continue
                if count[_scope][pair]["_total_"]["_total_"]:
                    total = count[_scope][pair]["_total_"]["_total_"]
                    acc[_scope][pair] = agree[_scope][pair] / count[_scope][pair]["_total_"]["_total_"]
                    acc1[_scope][pair] = agree1[_scope][pair] / count[_scope][pair]["_total_"]["_total_"]
                    acc2[_scope][pair] = agree2[_scope][pair] / count[_scope][pair]["_total_"]["_total_"]
                    acc3[_scope][pair] = agree3[_scope][pair] / count[_scope][pair]["_total_"]["_total_"]
                    expected = sum(count[_scope][pair][scene]["_total_"] * count[_scope][pair]["_total_"].get(scene, 0) for scene in count[_scope][pair].keys() if scene != "_total_") / count[_scope][pair]["_total_"]["_total_"]**2
                    cohen[_scope][pair] = (acc[_scope][pair] - expected) / (1 - expected)

                    print("\t".join(str(x) for x in (pair,
                                                     acc[_scope][pair], "({}/{})".format(agree[_scope][pair], total),
                                                     acc3[_scope][pair], "({}/{})".format(agree3[_scope][pair], total),
                                                     acc2[_scope][pair], "({}/{})".format(agree2[_scope][pair], total),
                                                     acc1[_scope][pair], "({}/{})".format(agree1[_scope][pair], total),
                                                     cohen[_scope][pair])))
            print("\n")





        print()

            
        ## Confusion matrices
        for _scope in ["scene"]: #, "function"]:

            print((len(_scope) + 4) * "#")
            print("# {} #".format(len(_scope)*" "))
            print("# {} #".format(_scope))
            print("# {} #".format(len(_scope)*" "))
            print((len(_scope) + 4) * "#")
            print()

            scope = count[_scope]
            scen = count["scene"]
            func = count["function"]

            for pair, matrix in sorted(scope.items()):
                if "_majority_" in pair:
                    continue
                print(pair)
                print()
                # u1, u2 = pair.split("|")
                # d1 = matrix.keys()
                # d2 = matrix["_total_"].keys()
                # dimensions = sorted(set(d1).union(set(d2)))
                # print("\t" + "\t".join(dimensions))
                conf2count = {"scene":{}, "function":{}}
                for i in range(len(dimensions)):
                    cat1 = dimensions[i]
    #                    if cat1 == "_total_":
    #                        continue
                    line = cat1
    #                    line = ""
                    for j in range(len(dimensions)):
                        cat2 = dimensions[j]
                        if pair == "_all_":
                            if j <= i:
                                c = matrix.get(cat1, {}).get(cat2, 0)
                                line += "\t{}".format(c)
                                if j < i:
                                    conf2count["scene"][cat1, cat2] = c
                            if j == i:
                                line += "\t\t"
                            if j >= i:
                                c = func["_all_"].get(cat1, {}).get(cat2, 0)
                                line += "\t{}".format(c)
                                if j > i:
                                    conf2count["function"][cat1, cat2] = c
                            
                        else:
                            
                            line += "\t{}".format(matrix.get(cat1, {}).get(cat2, 0))
                    print(line + "\t" + cat1)

                sorted_conf_scene = sorted((item for item in conf2count["scene"].items()), key=itemgetter(1), reverse=True)
                sorted_conf_func = sorted((item for item in conf2count["function"].items()), key=itemgetter(1), reverse=True)
                print("most frequent (scene): {}{}".format(sorted_conf_scene[:10], " ..." if len(sorted_conf_scene) > 10 else ""))
                print("most frequent (function): {}".format(sorted_conf_func[:10], " ..." if len(sorted_conf_func) > 10 else ""))
                print("\n")
            print("\n")
        # print(json.dumps(count, indent=True))

    return considered_units
        
if __name__ == "__main__":
    main(sys.argv[1:])
