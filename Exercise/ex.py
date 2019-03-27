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
        self.actions = utility
    def getUtility(self):
        uT = 0
        if(isinstance(self.actions, int)):
                uT += self.actions * self.prob
        else:
            for key in self.actions:
                #print(key, str(self.actions[key]))
                if(isinstance(self.actions[key], int)):
                    uT += self.actions[key] * self.prob
                else:
                    uT += self.actions[key].getUtility() * self.prob
        return uT
    def recalcProb(self):
        occ_total = 0
        for key in self.actions:
            occ_total += self.actions[key].occ
        for key in self.actions:
            self.actions[key].prob = self.actions[key].occ / occ_total


class Task:
    def __init__(self, actions):
        self.actions = actions
        #print(actions)
    def getUtility(self):
        uT = 0
        for key in self.actions:
            #print(key, self.actions[key].getUtility())
            uT += self.actions[key].getUtility()
        return uT
    def recalcProb(self):
        occ_total = 0
        for key in self.actions:
            occ_total += self.actions[key].occ
        for key in self.actions:
            self.actions[key].prob = self.actions[key].occ / occ_total

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
            #print(key, str(u))
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
    settings = re.findall(r"-?[0-9]+%?|\[.*\]", stri)
    #letters = re.findall(r"[^\[]][a-zA-Z]+", stri)
    
    if(len(settings[0]) > 2 and settings[0][len(settings[0])-1] == '%'):
        prob = int(settings[0][:len(settings[0])-1]) / 100
    else:
        occ = int(settings[0])
    if(settings[1][0] == '['):
        #print(settings[1])
        subActions = re.findall(r"-?[0-9]+%?,\[.*?\]|-?[0-9]+%?,-?[0-9]+", settings[1])
        subALetters = re.findall(r"[a-zA-Z][0-9]?", settings[1][1:])
        subALetters1 = re.findall(r"[a-zA-Z][0-9]", settings[1][1:])
        subALetters2 = re.findall(r"[a-zA-Z]", settings[1][1:])
        if(len(subALetters1) > 0 and subALetters1[0] == subALetters[0]):
            subALetters = subALetters1
        elif(len(subALetters2) > 0 and subALetters2[0] == subALetters[0]):
            subALetters = subALetters2
        #print("sub: ", subActions, subALetters)
        for i in range(len(subActions)):
            beliefs[subALetters[i]] = parseActionCond(subActions[i], subALetters[i])
    else:
        #print(letter, settings[1])
        beliefs[letter] = int(settings[1])
    #print(letter, beliefs)
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
        task_actions = re.findall(r"\(-?[0-9]+%?,-?[0-9]+\)|\(-?[0-9]+%?,\[.*\]\)", tasks[i][1:len(tasks[i])-1])
        letter = re.findall(r"[A-Z]", tasks[i][1:len(tasks[i])-1])[0]
        action_letters = []
        for k in range(len(task_actions)):
            action_letters.append(chr(ord(letter) + k))
        #print(task_actions, action_letters)
        occ_total = 0
        count_occ = False
        for j in range(len(task_actions)):
            actions[action_letters[j]] = parseActionCond(task_actions[j], action_letters[j])
            if(actions[action_letters[j]].occ != -1):
                occ_total += actions[action_letters[j]].occ
                count_occ = True
        if(count_occ):
            for key in actions:
                actions[key].prob = actions[key].occ / occ_total
        #print(letters[i], actions)
        res[letters[i]] = Task(actions)
    return res

def updateAction(line, agent):
    line_proc = line.split(",")
    unew = line_proc[0][1:]
    acts = line_proc[1][:len(line_proc[1])-1]
    rec = acts.split(".")
    action = agent.tasks[rec[0]]
    i=1
    for i in range(1, len(rec)-1):
        if(rec[i] in action.actions):
            action = action.actions[rec[i]]
    action.actions[rec[i]] = Action(-1, 1, int(unew))
    for key in action.actions:
        if(key == unew):
            continue
        if(action.actions[key].occ == -1):
            action.actions[key].occ = 0
    action.recalcProb()

#-------------------
# MAIN CODE
#-------------------

done = False
while(not done):
    line = str(input())
    line = line.split(" ")
    if(line[0] == "decide-rational"):
        done = False
        if(len(line) == 2):
            agent = RationalAgent(parseLineCond(line[1]), 1)
        elif(len(line) == 3):
            agent = RationalAgent(parseLineCond(line[1]), line[2])
        else:
            done = True
            print("Invalid Input.")
        print(agent.decide())
        while(not done):
            line = str(input())
            # TODO: Implement better end
            if(line == "end"):
                done = False
            else:
                updateAction(line, agent)
                print(agent.decide())
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
    