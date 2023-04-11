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
nHours = 100            # FINAL VERSION 8760
# Set of days
hours = range(0, nHours)  # 0 ... 8759

#### ADD DECISION VARIABLES

# Electrolyzer
CapacityElec = m.addVar(vtype = GRB.CONTINUOUS, name="CapasityElec")
MultiplyCapElec = m.addVars(hours, name="MultiplyCapElec") # multiply helper variable


# Wind
CapacityWind = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityWind") # Ostettu tuulen tuotantokapasiteetti (MW) PAP

WindProd = m.addVars(hours, name="WindProd") # multiply helper variable


# Solar

""" CapacitySolar = m.addVar(vtype = GRB.CONTINUOUS, name="CapacitySolar") # Ostettu aurinkovoiman tuotantokapasiteetti (MW) PAP

BaseProdSolar = m.addVar(vtype = GRB.CONTINUOUS, name="BaseProdSolar") # Tuntikohtainen tuotanto baseload sopimuksessa (vakio)

SolarProd = m.addVars(hours, name="SolarProd") # multiply helper variable """

# Battery

# Storage

# Grid

# Supporting variables

ElectrisityProd = m.addVar(vtype = GRB.CONTINUOUS, name="ElectrisityProd") # CapasityWind * CapFactorWind[h] + CapasitySolar * CapFactorSolar[h]

#### ADD PARAMETERS

# Demand 
Demand = np.zeros(nHours)     # nhours 
Demand[0:nHours-20] = 15000      # January-June production
Demand[nHours-10:nHours] = 15000      # January-June production
#Demand[5784:8760] = 15000   # July maintenance break and after full steam. KOMMENTTI POIS LOPULLISESSA

# Electrolyzer
CapexElec = 845     # € / kWe
OpexElec = 17       # € / kWe
EfficiencyElec = 64
Pup = 0.50  # 50% muutos maksimikapasiteetista tunnissa
## Pdown = 0.70  # 70% muutos maksimikapasiteetista tunnisssa TÄMÄ POIS?
RElec = 0.17
CapFactorElec = m.addVars(hours, ub=1, lb=0, name="CapFactorElec")  # CapFactor, current capacity x%



# Wind
PapPriceWind = 52   # PPA pay-as-produced hinta (€ / MWhh)
ElecTax = 0.63     # sähkönvero (€ / MWh)
#TransmisFee = ??   # sähkönsiirtomaksu (€ / MWh)

CapFactorWind = []  # Tuntikohtainen kapasiteettikerroin
for h in hours:
    n = random.random()  # rando capacity factor between 0 ... 1
    CapFactorWind.append(n)

# Solar
#PapPriceSolar = 1  # PPA pay-as-produced hinta (€ / MWh)
#BasePriceSolar = 0.3  # PPA baseload hinta (€ / MWh)

""" CapFactorSolar = []  # Tuntikohtainen kapasiteettikerroin
for h in hours:
    n = random.random()  # random demand between 0 ... 1
    CapFactorSolar.append(n) """

# Battery

# Storage

# Grid



#### ADD CONSTRAINTS

# Constraints for Pup and Pdown
m.addConstrs((CapFactorElec[i] <= (Pup + CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEIncreaseConstr")
m.addConstrs((CapFactorElec[i] >= (Pup - CapFactorElec[i - i]) for i in range(1, nHours)), name="CFEDecreaseConstr")

""" m.addConstrs((SolarProd[h]
              == (CapacitySolar * CapFactorSolar[h]) for h in range(0, nHours)), name="mulSolar") """
m.addConstrs((WindProd[h]
              == (CapacityWind * CapFactorWind[h]) for h in range(0, nHours)), name="mulWind")
m.addConstrs((MultiplyCapElec[h]
              == (CapacityElec * CapFactorElec[h]) for h in range(0, nHours)), name="mulElec")

# Production has to meet demand

# ei vielä auringolle dataa
""" m.addConstrs(((SolarProd[h] + BaseProdSolar)
              * EfficiencyElec * MultiplyCapElec[h] >= (Demand[h])
              for h in range(1, nHours + 1)), "*") """

m.addConstrs((WindProd[h] * EfficiencyElec * MultiplyCapElec[h] >= (Demand[h])
              for h in range(0, nHours)), "*")

#### SET OBJECTIVE
m.setObjective(((CapexElec*RElec + OpexElec)*CapacityElec 
                + gp.quicksum(PapPriceWind*(1+ElecTax)*CapFactorWind[h]*CapacityWind for h in range(1,nHours))), GRB.MINIMIZE)

#### OPTIMIZE

# NonConvex, quadratic equity constraints
m.Params.NonConvex = 2
m.optimize()
# m.printAttr("C")
for v in m.getVars ():
    print ('%s %g' % ( v . VarName , v . X ))
print ('Obj : %g' % m. ObjVal )