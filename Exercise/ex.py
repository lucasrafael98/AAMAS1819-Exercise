#-------------------
# IMPORTS
#-------------------
import json, re, sys
from math import sqrt
from pylinprog import linsolve

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
        if(isinstance(self.actions, int) or isinstance(self.actions, float)):
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
                if((isinstance(self.actions[key], int) or isinstance(self.actions[key], float)) and self.actions[key] < umin):
                    umin = self.actions[key]
                elif(self.actions[key].getMinUtility() < umin):
                    umin = self.actions[key].getMinUtility()
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
            if(self.actions[key].getMinUtility() < umin):
                umin = self.actions[key].getMinUtility()
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
class SingleAgent:
    def __init__(self, tasks):
        self.tasks = tasks
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
        action.actions[rec[i]] = Action(-1, 1, float(unew))
        for key in action.actions:
            if(key == unew):
                continue
            if(action.actions[key].occ == -1):
                action.actions[key].occ = 0
        action.recalcProb()

class RationalAgent(SingleAgent):
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

class RiskAgent(SingleAgent):
    def decide(self):
        keys = []
        uexp = []
        umin = [[]]
        for key in self.tasks:
            keys.append(key)
            uexp.append(-self.tasks[key].getExpectedUtility())
            umin[0].append(-self.tasks[key].getMinUtility()) # inverted because of linprog lib
        perc = [[1 if i==j else 0 for j in range(len(uexp))] for i in range(len(uexp))]
        print(uexp, umin+perc)
        print("eql", [[1]*len(uexp)])
        print("ineqr", [0]+[1]*len(uexp))
        print("nonneg", tuple(i for i in range(len(uexp))))
        reso, sol = linsolve(uexp, 
                            eq_left=[[1]*len(uexp)], eq_right=[1], 
                            ineq_left=umin+perc, 
                            ineq_right=[0]+[1]*len(uexp),
                            nonneg_variables=tuple(i for i in range(len(uexp))))
        print(reso, sol)
        res = "("
        for i in range(len(sol)):
            if(sol[i] >= 0.01):
                res += ("%0.2f" % sol[i]) + "," + keys[i] + ";" 
        res = res[:-1] + ")"""
        return res

class CondAgent(SingleAgent):
    def decide(self):
        return ""

class NashAgent(SingleAgent):
    def decide_row(self):
        rows = [None]*len(self.tasks)
        for i in range(len(self.tasks)):
            jmax, jidx = -1,-1
            for j in range(len(self.tasks)):
                if(self.tasks[i][j].getExpectedUtility() > jmax):
                    jmax = self.tasks[i][j].getExpectedUtility()
                    jidx = j
            rows[i] = (i, jidx)
        return rows
    def decide_col(self):
        cols = [None]*len(self.tasks)
        for i in range(len(self.tasks)):
            jmax, jidx = -1,-1
            for j in range(len(self.tasks)):
                if(self.tasks[j][i].getExpectedUtility() > jmax):
                    jmax = self.tasks[j][i].getExpectedUtility()
                    jidx = j
            cols[i] = (jidx, i)
        return cols

class MixedAgent(SingleAgent):
    def decide(self):
        return ""

# Describes a multi-agent system.
class MultiAgent:
    def __init__(self, mine, peer):
        self.mine = mine
        self.peer = peer
    def decide(self):
        rmine = self.mine.decide_row()
        cpeer = self.peer.decide_col()
        if(rmine[0] == cpeer[0] and rmine[1] == cpeer[1]):
            if(rmine[0] > rmine[1]):
                return "mine=T" + str(rmine[0][0]) + ",peer=T" + str(rmine[0][1])
            else:
                return "mine=T" + str(rmine[1][0]) + ",peer=T" + str(rmine[1][1])
        elif(rmine[0] == cpeer[0]):
            return "mine=T" + str(rmine[0][0]) + ",peer=T" + str(rmine[0][1])
        elif(rmine[1] == cpeer[1]):
            return "mine=T" + str(rmine[1][0]) + ",peer=T" + str(rmine[1][1])
        else:
            return "blank-decision"

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
    
def JSONise(stri):
    stri = "[{" + stri[1:-1] + "}]"
    stri = stri.replace("(", "").replace(")","")
    # transform into taskName
    stri = re.sub(r",(T[0-9]+(\|T[0-9]+)?)=\[", r'},{"taskName":"\1","actions":[{', stri)
    stri = re.sub(r"(T[0-9]+(\|T[0-9]+)?)=\[", r'"taskName":"\1","actions":[{', stri)
    # transform action and probability
    stri = re.sub(r",([A-Z][0-9]*)=(-?[0-9]+%?)", r'},{"actionName":"\1","probability":"\2"', stri)
    stri = re.sub(r"([A-Z][0-9]*)=(-?[0-9]+%?)", r'"actionName":"\1","probability":"\2"', stri)
    # transform utility
    stri = re.sub(r",(-?[0-9]+)\]", r',"utility":\1}]', stri)
    stri = re.sub(r",(-?[0-9]+)", r',"utility":\1', stri)
    stri = re.sub(r",\[", r',"utility":[{', stri)
    # some weird special case the above misses, ignore please
    stri = re.sub(r"\]\]", r"]}]", stri)
    return stri

def parseLineCond(stri):
    parsed = json.loads(JSONise(stri))
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

def parseMultiAgent(line):
    mtxsize = int(sqrt(len(line)))
    tasks = [[None for j in range(mtxsize)]for i in range(mtxsize)]
    for task in line:
        i, j = re.findall(r"T([0-9]+)", task["taskName"])
        i = int(i)
        j = int(j)
        taskActions = {}
        for action in task["actions"]:
            taskActions[action["actionName"]] = createAction(action)
            if(taskActions[action["actionName"]].prob == -1):
                hasOcc = True
        tasks[i][j] = Task(taskActions)
        if(hasOcc):
            tasks[i][j].recalcProb()
    return tasks

def parseLineMulti(stri):
    stri = stri.split(",peer=")
    sm = json.loads(JSONise(stri[0][5:]))
    sp = json.loads(JSONise(stri[1]))
    tmine = parseMultiAgent(sm)
    tpeer = parseMultiAgent(sp)
    return tmine, tpeer

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
        interaccs = 1
        if(len(line) == 2):
            agent = RationalAgent(parseLineCond(line[1]))
        elif(len(line) == 3):
            agent = RationalAgent(parseLineCond(line[1]))
            interaccs = line[2]
        else:
            done = True
            sys.stdout.write("Invalid Input.")
        sys.stdout.write(agent.decide() + "\n")
        sys.stdout.flush()
        update_done = False
        for i in range(interaccs):
            line = str(sys.stdin.readline())
            if(line == "ls"):
                agent.listTasks()
            else:
                agent.updateAction(line)
                sys.stdout.write(agent.decide() + "\n")
                sys.stdout.flush()
    elif(line[0] == "decide-risk"):
        if(len(line) == 2 or len(line) == 2):
            agent = RiskAgent(parseLineCond(line[1]))
        else:
            sys.stdout.write("Invalid Input.")
        sys.stdout.write(agent.decide() + "\n")
        sys.stdout.flush()
    elif(line[0] == "decide-conditional"):
        tmine, tpeer = parseLineMulti(line[1])
        mine = CondAgent(tmine)
        peer = CondAgent(tpeer)
        agents = MultiAgent(mine, peer)
        sys.stdout.write(agents.decide() + "\n")
        sys.stdout.flush()
    elif(line[0] == "decide-nash"):
        tmine, tpeer = parseLineMulti(line[1])
        mine = NashAgent(tmine)
        peer = NashAgent(tpeer)
        agents = MultiAgent(mine, peer)
        sys.stdout.write(agents.decide() + "\n")
        sys.stdout.flush()
    elif(line[0] == "decide-mixed"):
        tmine, tpeer = parseLineMulti(line[1])
        mine = MixedAgent(tmine)
        peer = MixedAgent(tpeer)
        agents = MultiAgent(mine, peer)
        sys.stdout.write(agents.decide() + "\n")
        sys.stdout.flush()
    else:
        done = True
    