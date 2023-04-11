# -*- coding: utf-8 -*-
# Optimization of hydrogen production price
import itertools
# Constrains: Production of hydrogen has to meet demand, the rest is "wasted"
# All optimized variables are real numbers >=0


import random

import gurobipy as gp
from gurobipy import GRB
import sys
import numpy as np       

#### CREATE MODEL
m = gp.Model("Hydrogen")

# number of hours
nHours = 100
# Set of days
hours = range(0, nHours)  # 0 ... 8760

#### ADD DECISION VARIABLES

# Electrolyzer
CapacityElec = m.addVar(vtype = GRB.CONTINUOUS, name="CapFactorElec")


# Wind

# Solar

CapacitySolar = m.addVar(vtype = GRB.CONTINUOUS, name="CapacitySolar") # Ostettu tuulen tuotantokapasiteetti (MW) PAP

BaseProdSolar = m.addVar(vtype = GRB.CONTINUOUS, name="BaseProdSolar") # Tuntikohtainen tuotanto baseload sopimuksessa (vakio)

MultiplyCapSolar = m.addVars(hours, name="MultiplyCapSolar") # multiply helper variable

# Battery

# Storage

# Grid



#### ADD PARAMETERS

# Demand 
#### ADD ####
# SELKEÄMPI JOS TASAINEN TUOTANTO? HEINÄKUULLE OLETETTU SEISOKKI
Demand = np.zeros(nHours)
Demand[0:nHours] = 15000      # July maintenance break
#Demand[5784:8760] = 15000   # July maintenance break

# Electrolyzer
CapexElec = 845     # € / kWe
OpexElec = 17       # € / kWe
EfficiencyElec = 64
Pup = 0.50  # 50% muutos maksimikapasiteetista tunnissa
Pdown = 0.70  # 70% muutos maksimikapasiteetista tunnisssa
RElec = 0.17
CapFactorElec = m.addVars(hours, ub=1, lb=0, name="CapFactorElec")  # CapFactor, current capacity x%   
# Multiply helper variable
MultiplyCapElec = m.addVars(hours, name="MultiplyCapElec")

# Wind


# Solar
PapPriceSolar = 1  # PPA pay-as-produced hinta (€ / MWh)
BasePriceSolar = 0.3  # PPA baseload hinta (€ / MWh)

CapFactorSolar = []  # Tuntikohtainen kapasiteettikerroin
for h in hours:
    n = random.random()  # random demand between 0 ... 1
    CapFactorSolar.append(n)

# Battery

# Storage

# Grid



#### ADD CONSTRAINTS

# Constraints for Pup and Pdown
m.addConstrs((CapFactorElec[i] <= (Pup + CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEIncreaseConstr")
m.addConstrs((CapFactorElec[i] >= (Pup - CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEDecreaseConstr")

m.addConstrs((MultiplyCapSolar[h]
              == (CapacitySolar * CapFactorSolar[h]) for h in range(1, nHours)), name="mul2")
m.addConstrs((MultiplyCapElec[h]
              == (CapacityElec * CapFactorElec[h]) for h in range(1, nHours)), name="mul1")

# Production has to meet demand
m.addConstrs(((MultiplyCapSolar[h] + BaseProdSolar)
              * EfficiencyElec * MultiplyCapElec[h] >= (Demand[h])
              for h in range(1, nHours)), "*")

#### SET OBJECTIVE
m.setObjective(((CapexElec*RElec + OpexElec)*CapacityElec), GRB.MINIMIZE)

#### OPTIMIZE

# NonConvex, quadratic equity constraints
m.Params.NonConvex = 2
m.optimize()
# m.printAttr("C")
for v in m.getVars ():
    print ('%s %g' % ( v . VarName , v . X ))
print ('Obj : %g' % m. ObjVal )
