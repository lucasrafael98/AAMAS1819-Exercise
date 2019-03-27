#-------------------
# IMPORTS
#-------------------

import re

#-------------------
# CLASSES
#-------------------

class Action:
    def __init__(self, prob, occ, utility):
        self.prob = prob
        self.occ = occ
        self.utility = utility
    def getUtility(self):
        uT = 0
        for key in self.utility:
            if(isinstance(self.utility[key], int)):
                uT += self.utility[key]
            else:
                uT += self.utility[key].getUtility()
        return uT

class Task:
    def __init__(self, actions):
        self.actions = actions
        #print(actions)
    def getUtility(self):
        uT = 0
        for key in self.actions:
            uT += self.actions[key].getUtility()
        return uT

class Agent:
    def __init__(self, tasks, interactions):
        self.tasks = tasks
        self.interaccs = interactions
        #print(tasks)

class RationalAgent(Agent):
    def decide(self):
        res = ""
        umax = 0
        for key in self.tasks:
            u = self.tasks[key].getUtility()
            #print(key + str(u))
            if(u > umax):
                umax = u
                res = key
        return res

class RiskAgent(Agent):
    def decide(self):
        # TODO: Implement
        return 1

#-------------------
# AUX FUNCTIONS
#-------------------

def parseActionCond(stri, letter):
    prob = -1
    occ = -1
    beliefs = {}
    #print(stri)
    settings = re.findall(r"-?[0-9]+%?|\[.*?\]", stri)
    #letters = re.findall(r"[^\[]][a-zA-Z]+", stri)
    
    if(len(settings[0]) > 2 and settings[0][len(settings[0])-1] == '%'):
        prob = int(settings[0][:len(settings[0])-1]) / 100
    else:
        occ = int(settings[0])
    if(settings[1][0] == '['):
        subActions = re.findall(r"-?[0-9]+%?,\[.*?\]|-?[0-9]+%?,-?[0-9]+", settings[1])
        subALetters = re.findall(r"[a-zA-Z][0-9]*", settings[1][1:])
        #print("sub: ", subActions, subALetters)
        for i in range(len(subActions)):
            beliefs[subALetters[i]] = parseActionCond(subActions[i], subALetters[i])
    else:
        #print(letter, settings[1])
        beliefs[letter] = int(settings[1])
    #print(beliefs)
    return Action(prob, occ, beliefs)
    

def parseLineCond(stri):
    res = {}
    stri = stri[1:len(stri) - 1]
    # each task's action is parsed here.
    tasks = re.split(r',?T.=', stri)[1:]
    letters = re.findall(r"T[0-9]+", stri)
    #print(tasks)
    #print(stri)
    #print(letters)
    for i in range(len(tasks)):
        actions = {}
        task_actions = re.findall(r"\(-?[0-9]+%?,-?[0-9]+\)|\(-?[0-9]+%?,\[.*?\]\)", tasks[i][1:len(tasks[i])-1])
        action_letters = re.findall(r"[A-Z]", tasks[i][1:len(tasks[i])-1])
        #print(task_actions)
        
        for j in range(len(task_actions)):
            actions[action_letters[j]] = parseActionCond(task_actions[j], action_letters[j])
        res[letters[i]] = Task(actions)
    return res


#-------------------
# MAIN CODE
#-------------------

done = False
while(not done):
    line = str(input())
    line = line.split(" ")
    if(line[0] == "decide-rational"):
        if(len(line) == 2):
            agent = RationalAgent(parseLineCond(line[1]), 1)
        elif(len(line) == 3):
            agent = RationalAgent(parseLineCond(line[1]), line[2])
        else:
            print("Invalid Input.")
    elif(line[0] == "decide-risk"):
        if(len(line) == 2):
            agent = RiskAgent(parseLineCond(line[1]), 1)
        elif(len(line) == 3):
            agent = RiskAgent(parseLineCond(line[1]), line[2])
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
    print(agent.decide())
    