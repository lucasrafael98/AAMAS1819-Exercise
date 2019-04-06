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
                if(isinstance(self.actions, int) or isinstance(self.actions, float)):
                    uT += self.actions[key] * self.prob
                else:
                    uT += self.actions[key].getExpectedUtility() * self.prob
        return uT
    def getMinUtility(self):
        if(isinstance(self.actions, int) or isinstance(self.actions, float)):
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
    def listActions(self):
        stri = ""
        if(isinstance(self.actions, int) or isinstance(self.actions, float)):
            stri += str(self.getExpectedUtility()) +"\n"
        else:
            for key in self.actions:
                stri += key + "\t" + str(self.actions[key].prob) \
                            + "\t" + str(self.actions[key].listActions()) +"\n"
        return stri
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
                        + "\t" + str(self.actions[key].listActions()) +"\n"
        return stri

# Describes an abstract agent that contains tasks.
class SingleAgent:
    def __init__(self, tasks):
        self.tasks = tasks
        self.lastDec = ""
        #print(tasks)
    def listTasks(self):
        for key in self.tasks:
            print(key, ("\n" + self.tasks[key].listActions()))
    def updateAction(self, line):
        line_proc = line.split(",")
        unew = line_proc[0][1:]
        acts = line_proc[1][:len(line_proc[1])-1]
        rec = acts.split(".")
        action = self.tasks[self.lastDec]
        i=0
        for i in range(0, len(rec)-2):
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
        umax = -1e8
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
        min_counts = 0
        for key in sorted(self.tasks):
            keys.append(key)
            uexp.append(-self.tasks[key].getExpectedUtility())
            umin[0].append(-self.tasks[key].getMinUtility()) # inverted because of linprog lib
            if(umin[0][-1] > 0):
                min_counts += 1
        eql = [[1 for i in range(len(uexp))]]
        eqr = [1]
        if(min_counts == len(umin[0])):
            ineqr = [min(umin[0]) + 1e-8]
        else:
            ineqr = [0]
        nonneg = list(range(len(uexp)))
        #print("obj", uexp)
        #print("eql", eql)
        #print("eql", eqr)
        #print("ineql", umin)
        #print("ineqr", ineqr)
        #print("nonneg", nonneg)
        sol = linsolve(uexp, 
                            eq_left=eql, eq_right=eqr, 
                            ineq_left=umin, 
                            ineq_right=ineqr,
                            nonneg_variables=nonneg)
        #print(sol)
        sol = sol[1]
        if(sol == None):
            return ""
        res = "("
        for i in range(len(sol)):
            count = 1
            lst = [i]
            for j in range(len(sol)):
                if(uexp[i] == uexp[j] and \
                    ((umin[0][i] >= 0 and  umin[0][j] >= 0) or (umin[0][i] <= 0 and  umin[0][j] <= 0))\
                    and sol[j] == 0):
                    count += 1
                    lst.append(j)
            s = sol[i]
            for k in lst:
                sol[k] = s / count
        for l in range(len(sol)):
            if(sol[l] >= 0.01):
                res += ("%0.2f" % sol[l]) + "," + keys[l] + ";" 
        res = res[:-1] + ")"""
        return res

class NashAgent(SingleAgent):
    def decide_row(self):
        rows = [None]*len(self.tasks)
        for i in range(len(self.tasks)):
            jmax, jidx = -1e8,-1
            for j in range(len(self.tasks[0])):
                if(self.tasks[i][j].getExpectedUtility() > jmax):
                    jmax = self.tasks[i][j].getExpectedUtility()
                    jidx = j
            rows[i] = (i, jidx)
        return rows
    def decide_col(self):
        cols = [None]*len(self.tasks[0])
        for i in range(len(self.tasks[0])):
            jmax, jidx = -1e8,-1
            for j in range(len(self.tasks)):
                if(self.tasks[j][i].getExpectedUtility() > jmax):
                    jmax = self.tasks[j][i].getExpectedUtility()
                    jidx = j
            cols[i] = (jidx, i)
        return cols

class MixedAgent(SingleAgent):
    def decide_row(self):
        a = self.tasks[0][0].getExpectedUtility()
        b = self.tasks[0][-1].getExpectedUtility()
        c = self.tasks[-1][0].getExpectedUtility()
        d = self.tasks[-1][-1].getExpectedUtility()
        #print(a,b,c,d)
        if(a-b-c+d == 0):
            return "blank-decision"
        p = (d-b)/(a-b-c+d)
        #print("%0.2f"%p, "%0.2f"%(1-p))
        if(p < 0 or p > 1):
            return "blank-decision"
        return ("%0.2f"%p, "%0.2f"%(1-p))
    def decide_col(self):
        a = self.tasks[0][0].getExpectedUtility()
        b = self.tasks[-1][0].getExpectedUtility()
        c = self.tasks[0][-1].getExpectedUtility()
        d = self.tasks[-1][-1].getExpectedUtility()
        #print(a,b,c,d)
        if(a-b-c+d == 0):
            return "blank-decision"
        p = (d-b)/(a-b-c+d)
        #print("%0.2f"%p, "%0.2f"%(1-p))
        if(p < 0 or p > 1):
            return "blank-decision"
        return ("%0.2f"%p, "%0.2f"%(1-p))

# Describes a multi-agent system.
class MultiAgent:
    def __init__(self, mine, peer):
        self.mine = mine
        self.peer = peer
    def decide_nash(self):
        cpeer = self.mine.decide_col()
        rmine = self.peer.decide_col()
        #print(rmine, cpeer)
        res = list(set(rmine).intersection(cpeer))
        if(len(res) == 0):
            return "blank-decision"
        if(len(res) == 1):
            return "mine=T" + str(res[0][0]) + ",peer=T" + str(res[0][1])
        else:
            rmax, ridx = -1e8, -1
            for r in res:
                #print(r[0], r[1], self.mine.tasks[r[0]][r[1]].getExpectedUtility() + self.peer.tasks[r[0]][r[1]].getExpectedUtility())
                if(self.mine.tasks[r[0]][r[1]].getExpectedUtility() +\
                    self.peer.tasks[r[0]][r[1]].getExpectedUtility() > rmax):
                    rmax = self.mine.tasks[r[0]][r[1]].getExpectedUtility() +\
                        self.peer.tasks[r[0]][r[1]].getExpectedUtility()
                    ridx = r
            return "mine=T" + str(ridx[0]) + ",peer=T" + str(ridx[1])
    def decide_mixed(self):
        rpeer = self.mine.decide_row()
        cmine = self.peer.decide_row()
        if(cmine == "blank-decision" or rpeer == "blank-decision"):
            return "blank-decision"
        return "mine=(" + cmine[0] + "," + cmine[1] + "),peer=("  + rpeer[0] + "," + rpeer[1] + ")"
    def decide_cond(self):
        nash = self.decide_nash()
        if(nash != "blank-decision"):
            return nash
        else:
            self.mine.__class__ = MixedAgent
            self.peer.__class__ = MixedAgent
            return self.decide_mixed()
    

#-------------------
# AUX FUNCTIONS
#-------------------

def createAction(dict):
    prob = -1
    occ = -1
    hasOcc = False
    if(dict["probability"][-1] == "%"):
        prob = float(dict["probability"][:-1]) / 100
    else:
        occ = int(dict["probability"])
    if(isinstance(dict["utility"], int) or isinstance(dict["utility"], float)):
        u = dict["utility"]
    else:
        u = {}
        for ac in dict["utility"]: 
            u[ac["actionName"]] = createAction(ac)
            if(u[ac["actionName"]].prob == -1):
                hasOcc = True
    action = Action(prob, occ, u)
    if(hasOcc):
        action.recalcProb()
    return action
    
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
    stri = re.sub(r",(-?[0-9]+(\.[0-9]+)?)\]", r',"utility":\1}]', stri)
    stri = re.sub(r",(-?[0-9]+(\.[0-9]+)?)\]", r',"utility":\1}]', stri)
    stri = re.sub(r",(-?[0-9]+(\.[0-9]+)?)", r',"utility":\1', stri)
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
    tasks = [\
                [None for j in range(int(line[-1]["taskName"][4]) + 1)]\
            for i in range(int(line[-1]["taskName"][1]) + 1)]
    for task in line:
        i, j = re.findall(r"T([0-9]+)", task["taskName"])
        i = int(i)
        j = int(j)
        taskActions = {}
        hasOcc = False
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
    print(agent.decide())
    update_done = False
    for i in range(1,int(interaccs)):
        line = str(sys.stdin.readline())
        if(line == "ls"):
            agent.listTasks()
        else:
            agent.updateAction(line)
            print(agent.decide())
elif(line[0] == "decide-risk"):
    if(len(line) == 2 or len(line) == 2):
        agent = RiskAgent(parseLineCond(line[1]))
    else:
        print("Invalid Input.")
    print(agent.decide())
elif(line[0] == "decide-conditional"):
    tmine, tpeer = parseLineMulti(line[1])
    mine = NashAgent(tmine)
    peer = NashAgent(tpeer)
    agents = MultiAgent(mine, peer)
    print(agents.decide_cond())
elif(line[0] == "decide-nash"):
    tmine, tpeer = parseLineMulti(line[1])
    mine = NashAgent(tmine)
    peer = NashAgent(tpeer)
    agents = MultiAgent(mine, peer)
    print(agents.decide_nash())
elif(line[0] == "decide-mixed"):
    tmine, tpeer = parseLineMulti(line[1])
    mine = MixedAgent(tmine)
    peer = MixedAgent(tpeer)
    agents = MultiAgent(mine, peer)
    print(agents.decide_mixed())
    