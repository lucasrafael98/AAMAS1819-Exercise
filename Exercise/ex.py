#-------------------
# IMPORTS
#-------------------

import json, re

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
    def getUtility(self):
        uT = 0
        for key in self.actions:
            uT += self.actions[key].getUtility()
        return uT
    def recalcProb(self):
        occ_total = 0
        for key in self.actions:
            occ_total += self.actions[key].occ
        for key in self.actions:
            self.actions[key].prob = self.actions[key].occ / occ_total
    def listActions(self):
        stri = ""
        for key in self.actions:
            stri += key + "\t" + str(self.actions[key].prob) \
                         + "\t" + str(self.actions[key].getUtility()) +"\n"
        return stri

class Agent:
    def __init__(self, tasks, interactions):
        self.tasks = tasks
        self.interaccs = interactions
        #print(tasks)
    def listTasks(self):
        for key in self.tasks:
            print(key, ("\n" + self.tasks[key].listActions()))

class RationalAgent(Agent):
    def decide(self):
        res = ""
        umax = 0
        for key in self.tasks:
            u = self.tasks[key].getUtility()
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

def createAction(dict):
    prob = -1
    occ = -1
    if(dict["probability"][-1] == "%"):
        prob = float(dict["probability"][:-1]) / 100
    else:
        occ = int(dict["probability"])
    if(isinstance(dict["utility"], int)):
        u = dict["utility"]
    else:
        u = {}
        for ac in dict["utility"]: 
            u[ac["actionName"]] = createAction(ac)
    return Action(prob, occ, u)
    
def parseLineCond(stri):
    stri = "[{" + stri[1:-1] + "}]"
    stri = stri.replace("(", "").replace(")","")
    # transform into taskName
    stri = re.sub(r",(T[0-9]+)=\[", r'},{"taskName":"\1","actions":[{', stri)
    stri = re.sub(r"(T[0-9]+)=\[", r'"taskName":"\1","actions":[{', stri)
    # transform action and probability
    stri = re.sub(r",([A-Z][0-9]*)=(-?[0-9]+%?)", r'},{"actionName":"\1","probability":"\2"', stri)
    stri = re.sub(r"([A-Z][0-9]*)=(-?[0-9]+%?)", r'"actionName":"\1","probability":"\2"', stri)
    # transform utility
    stri = re.sub(r",(-?[0-9]+)\]\}", r',"utility":\1}]}', stri)
    stri = re.sub(r",(-?[0-9]+)", r',"utility":\1', stri)
    stri = re.sub(r",\[", r',"utility":[{', stri)
    # lol idk either
    stri = re.sub(r"\]\]", r'}]}]', stri)
    parsed = json.loads(stri)
    tasks = {}
    for task in parsed:
        hasOcc = False
        taskActions = {}
        for action in task["actions"]:
            taskActions[action["actionName"]] = createAction(action)
            if(taskActions[action["actionName"]].prob == -1):
                hasOcc = True
        tasks[task["taskName"]] = Task(taskActions)
        if(hasOcc):
            tasks[task["taskName"]].recalcProb()
    return tasks

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
    line = str(input("console> "))
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
        update_done = False
        while(not update_done):
            line = str(input("console> "))
            # TODO: Implement better end
            if(line == "end"):
                update_done = True
            if(line == "ls"):
                agent.listTasks()
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
    