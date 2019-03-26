import re
#-------------------
# CLASSES
#-------------------
class Action:
    def __init__(self, prob, occ, belief):
        self.prob = prob
        self.occ = occ
        self.belief = belief

class Task:
    def __init__(self, actions):
        self.actions = actions

class Agent:
    def __init__(self, tasks, interactions):
        self.tasks = tasks
        self.interaccs = interactions

class RationalAgent(Agent):
    def decide(self):
        # TODO: Implement
        return 1

class RiskAgent(Agent):
    def decide(self):
        # TODO: Implement
        return 1

#-------------------
# AUX FUNCTIONS
#-------------------

def parseAction(str):
    prob = -1
    occ = -1
    beliefs = []
    #print(str)
    settings = re.findall(r"-?[0-9]+%?|\[.*?\]", str)
    #print(settings)
    if(len(settings[0]) > 2 and settings[len(settings)-1] == '%'):
        prob = int(settings[0][:len(settings)-1])
    else:
        occ = int(settings[0])
    if(settings[1][0] == '['):
        subActions = re.findall(r"-?[0-9]+%?,\[.*?\]|-?[0-9]+%?,-?[0-9]+", settings[1])
        #print("sub: ", subActions)
        for i in range(len(subActions)):
            beliefs.append(parseAction(subActions[i]))
    else:
        beliefs = int(settings[1])
    return Action(prob, occ, beliefs)
    

def parseLine(str):
    tasks = []
    str = str[1:len(str) - 1]
    # each task's action is parsed here.
    tasks = re.split(r',?T.=', str)[1:]
    for i in range(len(tasks)):
        actions = []
        task_actions = re.findall(r"\(-?[0-9]+%?,-?[0-9]+\)|\(-?[0-9]+%?,\[.*?\]\)", tasks[i][1:len(tasks[i])-1])
        for i in range(len(task_actions)):
            parseAction(task_actions[i])
        tasks.append(Task(actions))


#-------------------
# MAIN CODE
#-------------------

done = False
while(not done):
    line = str(input())
    line = line.split(" ")
    if(line[0] == "decide-rational"):
        if(len(line) == 2):
            agent = RationalAgent(parseLine(line[1]), 1)
        elif(len(line) == 3):
            agent = RationalAgent(parseLine(line[1]), line[2])
        else:
            print("Invalid Input.")
    elif(line[0] == "decide-risk"):
        if(len(line) == 2):
            agent = RiskAgent(parseLine(line[1]), 1)
        elif(len(line) == 3):
            agent = RiskAgent(parseLine(line[1]), line[2])
        else:
            print("Invalid Input.")
    elif(line[0] == "decide-conditional"):
        print("cond")
    elif(line[0] == "decide-nash"):
        print("nash")
    elif(line[0] == "decide-mixed"):
        print("mixed")
    else:
        done = True
    