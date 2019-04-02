#-------------------
# IMPORTS
#-------------------

import json, re, sys, pulp

#-------------------
# CLASSES
#-------------------

# Describes an action, which contains probability/occurrence number, 
# and utility, which might be a number or further actions.
class Action:
    def __init__(self, prob, occ, utility):
        self.prob = prob
        self.occ = occ
        self.actions = utility
    def getExpectedUtility(self):
        uT = 0
        if(isinstance(self.actions, int)):
                uT += self.actions * self.prob
        else:
            for key in self.actions:
                if(isinstance(self.actions[key], int)):
                    uT += self.actions[key] * self.prob
                else:
                    uT += self.actions[key].getExpectedUtility() * self.prob
        return uT
    def getMinUtility(self):
        if(isinstance(self.actions, int)):
                return self.actions
        else:
            umin = 1e32
            for key in self.actions:
                if(isinstance(self.actions[key], int) and self.actions[key] < umin):
                    umin = self.actions[key]
                elif(self.actions[key].getExpectedUtility() < umin):
                    umin = self.actions[key].getExpectedUtility()
        return umin
    def recalcProb(self):
        occ_total = 0
        for key in self.actions:
            occ_total += self.actions[key].occ
        for key in self.actions:
            self.actions[key].prob = self.actions[key].occ / occ_total

# Describes a task that contains actions.
class Task:
    def __init__(self, actions):
        self.actions = actions
    def getExpectedUtility(self):
        uT = 0
        for key in self.actions:
            uT += self.actions[key].getExpectedUtility()
        return uT
    def getMinUtility(self):
        umin = 1e32
        for key in self.actions:
            if(self.actions[key].getExpectedUtility() < umin):
                umin = self.actions[key].getExpectedUtility()
        return umin
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
                         + "\t" + str(self.actions[key].getExpectedUtility()) +"\n"
        return stri

# Describes an abstract agent that contains tasks.
class Agent:
    def __init__(self, tasks, interactions):
        self.tasks = tasks
        self.interaccs = interactions
        self.lastDec = ""
        #sys.stdout.write(tasks)
    def listTasks(self):
        for key in self.tasks:
            sys.stdout.write(key, ("\n" + self.tasks[key].listActions()))
    def updateAction(self, line):
        line_proc = line.split(",")
        unew = line_proc[0][1:]
        acts = line_proc[1][:len(line_proc[1])-1]
        rec = acts.split(".")
        action = self.tasks[self.lastDec]
        i=0
        for i in range(0, len(rec)-1):
            if(rec[i] in action.actions):
                action = action.actions[rec[i]]
        action.actions[rec[i]] = Action(-1, 1, int(unew))
        for key in action.actions:
            if(key == unew):
                continue
            if(action.actions[key].occ == -1):
                action.actions[key].occ = 0
        action.recalcProb()

class RationalAgent(Agent):
    def decide(self):
        res = ""
        umax = 0
        for key in self.tasks:
            u = self.tasks[key].getExpectedUtility()
            if(u > umax):
                umax = u
                res = key
        self.lastDec = res
        return res

class RiskAgent(Agent):
    def decide(self):
        uexp = {}
        umin = {}
        for key in self.tasks:
            uexp[key] = self.tasks[key].getExpectedUtility()
            umin[key] = self.tasks[key].getMinUtility()
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
    stri = re.sub(r",(-?[0-9]+)\]", r',"utility":\1}]', stri)
    stri = re.sub(r",(-?[0-9]+)", r',"utility":\1', stri)
    stri = re.sub(r",\[", r',"utility":[{', stri)
    # some weird special case the above misses, ignore please
    stri = re.sub(r"\]\]", r']}]', stri)
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

#-------------------
# MAIN CODE
#-------------------

done = False
while(not done):
    #line = str(input("console> "))
    line = str(sys.stdin.readline())
    line = line.split(" ")
    if(line[0] == "decide-rational"):
        done = False
        if(len(line) == 2):
            agent = RationalAgent(parseLineCond(line[1]), 1)
        elif(len(line) == 3):
            agent = RationalAgent(parseLineCond(line[1]), line[2])
        else:
            done = True
            sys.stdout.write("Invalid Input.")
        sys.stdout.write(agent.decide() + "\n")
        sys.stdout.flush()
        update_done = False
        while(not update_done):
            # line = str(input("console> "))
            line = str(sys.stdin.readline())
            # TODO: Implement better end
            if(line == "end"):
                update_done = True
            if(line == "ls"):
                agent.listTasks()
            else:
                agent.updateAction(line)
                sys.stdout.write(agent.decide() + "\n")
                sys.stdout.flush()
    elif(line[0] == "decide-risk"):
        if(len(line) == 2):
            agent = RiskAgent(parseLineCond(line[1]), 1)
        elif(len(line) == 3):
            agent = RiskAgent(parseLineCond(line[1]), line[2])
        else:
            sys.stdout.write("Invalid Input.")
        sys.stdout.write(agent.decide())
    elif(line[0] == "decide-conditional"):
        sys.stdout.write("cond")
    elif(line[0] == "decide-nash"):
        sys.stdout.write("nash")
    elif(line[0] == "decide-mixed"):
        sys.stdout.write("mixed")
    else:
        done = True
    