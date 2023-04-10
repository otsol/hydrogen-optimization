# Optimization of hydrogen production price
import itertools
# Constrains: Production of hydrogen has to meet demand, the rest is "wasted"
# All optimized variables are real numbers >=0


import random

import gurobipy as gp
from gurobipy import GRB
import sys

m = gp.Model("Hydrogen")

# Sample data
# number of hours
nHours = 1000
# Set of days
hours = range(0, nHours)  # 0 ... 23

# hourly demand for hydrogen, MWh
Dh = []
# Dh.append(0.0)  # start index for list operations
for h in hours:
    n = random.uniform(3, 11)  # random demand between 3 ... 10 MWh
    Dh.append(n)

# Wind Pay-As-Produced
PapPriceSolar = 1  # PPA pay-as-produced hinta (€ / MWh)
CapFactorSolar = []  # Tuntikohtainen kapasiteettikerroin
for h in hours:
    n = random.random()  # random demand between 0 ... 1
    CapFactorSolar.append(n)

# Wind baseload
BasePriceSolar = 0.3  # PPA baseload hinta (€ / MWh)

# Electrolyzer
CapexElec = 0.06
OpexElec = 0.03
EfficiencyElec = 0.9
Pup = 0.50  # 50% muutos maksimikapasiteetista tunnissa
Pdown = 0.70  # 70% muutos maksimikapasiteetista tunnisssa

# Decision variable CapacitySolar, Ostettu tuulen tuotantokapasiteetti (MW) PAP
CapacitySolar = m.addVar(name="CapacitySolar")
# Decision variable BaseProdSolar, Tuntikohtainen tuotanto baseload sopimuksessa (vakio)
BaseProdSolar = m.addVar(name="BaseProdSolar")
# multiply helper variable
MultiplyCapSolar = m.addVars(hours, name="MultiplyCapSolar")

# Decision variable HydrogenProduction

# Decision variable Electrolyzer
CapFactorElec = m.addVars(hours, ub=1, lb=0, name="CapFactorElec")  # CapFactor, current capacity x%
CapacityElec = m.addVar(name="CapFactorElec")
# Multiply helper variable
MultiplyCapElec = m.addVars(hours, name="MultiplyCapElec")

# Decision variable Cost, Vedyn litrahinta
Cost = m.addVar(name="Cost")

# Tavoite: Vedyn litrahinnan minimointi
m.setObjective((1.0 * CapexElec + 1.0 * OpexElec) * CapacityElec, GRB.MINIMIZE)

# m.addConstr(-Cost + CapexElec)

# Constraints for Pup and Pdown
m.addConstrs((CapFactorElec[i] <= (Pup + CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEIncreaseConstr")
m.addConstrs((CapFactorElec[i] >= (Pup - CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEDecreaseConstr")

m.addConstrs((MultiplyCapSolar[h]
              == (CapacitySolar * CapFactorSolar[h]) for h in range(1, nHours)), name="mul2")
m.addConstrs((MultiplyCapElec[h]
              == (CapacityElec * CapFactorElec[h]) for h in range(1, nHours)), name="mul1")

# Production has to meet demand
m.addConstrs(((MultiplyCapSolar[h] + BaseProdSolar)
              * EfficiencyElec * MultiplyCapElec[h] == (Dh[h])
              for h in range(1, nHours)), "*")


# NonConvex, quadratic equity constraints
m.Params.NonConvex = 2
m.optimize()
# m.printAttr("C")
print()
