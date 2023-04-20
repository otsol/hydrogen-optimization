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
import matplotlib.pyplot as plt

#### CREATE MODEL
m = gp.Model("Hydrogen")

# number of hours
nHours = 100            # FINAL VERSION 8760
# Set of days
# hours = range(0, nHours)  # 0 ... 8759
hours = np.arange(0, nHours)

#### ADD DECISION VARIABLES

# Electrolyzer
CapacityElec = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityElec")
#PowerElec = m.addVars(hours, name="PowerElec") # multiply helper variable POIS??
HydrogenProd = m.addMVar(nHours, name="HydrogenProd") # Hourly hydrogen production (kg)

# Wind
CapacityWind = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityWind") # Ostettu tuulen tuotantokapasiteetti (MW) PAP
WindProd = m.addVars(hours, name="WindProd") # multiply helper variable


# Solar

""" CapacitySolar = m.addVar(vtype = GRB.CONTINUOUS, name="CapacitySolar") # Ostettu aurinkovoiman tuotantokapasiteetti (MW) PAP

BaseProdSolar = m.addVar(vtype = GRB.CONTINUOUS, name="BaseProdSolar") # Tuntikohtainen tuotanto baseload sopimuksessa (vakio)

SolarProd = m.addVars(hours, name="SolarProd") # multiply helper variable """

# Battery
CapacityBattery = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityBattery")
ElectricityStored = m.addMVar(nHours, name="ElectricityStored")  # Hourly battery level



# Storage
CapacityStorage = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityStorage") # Hydrogen storage capacity (kg)
HydrogenStored = m.addMVar(nHours, name="HydrogenStored") # Hourly storage level of hydrogen(kg)

# Grid
ElectricitySold = m.addMVar(nHours, name="ElectricitySold") # Hourly sales of electricity

# Supporting variables

ElectricityProd = m.addMVar(nHours, name="ElectrisityProd") # CapasityWind * CapFactorWind[h] + CapasitySolar * CapFactorSolar[h]

#### ADD PARAMETERS

# Demand 
Demand = np.zeros(nHours)     # hourly demand
Demand[0:nHours-20] = 2000      # January-June production
Demand[nHours-10:nHours] = 2000     
#Demand[5784:8760] = 15000   # July maintenance break and after full steam. KOMMENTTI POIS LOPULLISESSA

# Electrolyzer
CapexElec = 850000     # € / MWe 
OpexElec = 17000       # € / MWe
EfficiencyElec = 16 # kg H2 / MWHe     
Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
RElec = 0.17
""" CapFactorElec = m.addVars(hours, ub=1, lb=0, name="CapFactorElec")  # CapFactor, current capacity x% """



# Wind
PapPriceWind = 52   # PPA pay-as-produced hinta (€ / MWhh)
ElecTax = 0.63     # sähkönvero (€ / MWh)
TransmisFee = 4.0   # sähkönsiirtomaksu (€ / MWh) PÄIVITÄ KUN DATAA

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
DepthOfDischarge = 0.8
CapexBattery = 378798
OpexBattery = 7576
ChargeEfficiency = 0.93
ChargePowerPerc = 0.43  # Charge rate as a ratio of max capacity

# Storage
CapexStorage = 80.90  # € / kg PÄIVITÄ KUN DATAA
OpexStorage = 3.24     # € / kg PÄIVITÄ KUN DATAA
RStorage = 0.36     # interest rate PÄIVITÄ KUN DATAA

# Grid
GridPrice = []  # Tuntikohtainen kapasiteettikerroin
for h in hours:
    n = random.random()*80  # rando capacity factor between 0 ... 80
    GridPrice.append(n)


#### ADD CONSTRAINTS

# Constrain definitions for supporting variables
m.addConstrs((WindProd[h]
              == (CapacityWind * CapFactorWind[h]) for h in range(0, nHours)), name="mulWind")

## LISÄÄ SUMMAAN SolarProd[h]
m.addConstrs((ElectricityProd[h]
              == (WindProd[h]) for h in range(0, nHours)), name="ElectricityProdConstr")

# Production and change in storage needs to meet demand
m.addConstrs((Demand[h]
              == (HydrogenProd[h] + HydrogenStored[h-1] - HydrogenStored[h]) for h in range(1, nHours)), name="DemandConstr")

# There needs to be enough electricity for hydrogen production HUOM! LISÄTÄÄN ELECTRISITY SOLD JA AKUN MUUTOKSEN VAIKUTUS TÄHÄN
m.addConstrs((HydrogenProd[h]
              == (ElectricityProd[h] - ElectricitySold[h] + ElectricityStored[h - 1] - ElectricityStored[h]) * EfficiencyElec for h in range(0, nHours)), name="ElectricityForProdConstr")

# Hydrogen production cannot exceed capacity
m.addConstrs((HydrogenProd[h]
              <= CapacityElec * EfficiencyElec for h in range(0, nHours)), name="HydrogenProdCapacityConstr")

# Constraints for Pchange 
m.addConstrs((HydrogenProd[h] - HydrogenProd[h-1] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PupConstr")
m.addConstrs((HydrogenProd[h-1] - HydrogenProd[h] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PdownConstr")

# Hydrogen storage cannot exceed capacity. Initial condition = 0
m.addConstrs((HydrogenStored[h] <= CapacityStorage for h in range(1, nHours)), name="CapacityStorageConstr")
m.addConstr((HydrogenStored[0] == 0), name="StorageInitConditionConstr")

# Electricity balance
m.addConstrs((ElectricityProd[h] - HydrogenProd[h] * (1 / EfficiencyElec) - ElectricitySold[h] == 0 for h in range(0, nHours)), name="ElectricityBalanceConstr")

# Battery constraints
m.addConstr((ElectricityStored[0] == 0), name="BatteryInitConditionConstr")  # Battery starts empty
m.addConstrs((ElectricityStored[h] <= CapacityBattery*DepthOfDischarge for h in range(0, nHours)), name="CapacityBatteryConstr")  # Max battery level 80%
m.addConstrs((ElectricityStored[h]-ElectricityStored[h-1] <= ChargePowerPerc*CapacityBattery*ChargeEfficiency for h in range(1, nHours)), name="BchangeConstr")
m.addConstrs((ElectricityStored[h-1]-ElectricityStored[h] <= ChargePowerPerc*CapacityBattery*ChargeEfficiency for h in range(1, nHours)), name="BchangeConstr")

""" m.addConstrs((SolarProd[h]
              == (CapacitySolar * CapFactorSolar[h]) for h in range(0, nHours)), name="mulSolar") """

#### SET OBJECTIVE
m.setObjective(((CapexElec*RElec + OpexElec)*CapacityElec + (CapexStorage * RStorage + OpexStorage)*CapacityStorage
                + gp.quicksum((PapPriceWind+ElecTax+TransmisFee)*CapFactorWind[h]*CapacityWind for h in range(0,nHours))
                - gp.quicksum((GridPrice[h]+ElecTax+TransmisFee)*ElectricitySold[h] for h in range(0,nHours))
                ), GRB.MINIMIZE)

#### OPTIMIZE

# NonConvex, quadratic equity constraints
m.Params.NonConvex = 2
m.optimize()
# m.printAttr("C")
# plt.figure(1)
for index, v in enumerate(m.getVars()):
    # plt.scatter(index, v.X)
    # plt.title(v.VarName)
    print('%s %g' % (v.VarName, v.X))
print('Obj : %g' % m.ObjVal)

if m.SolCount > 0:  # avoid attribute error if no feasible point is available
    plt.figure(2)
    res1 = HydrogenStored.X
    res2 = HydrogenProd.X
    res3 = CapacityStorage.X
    plt.plot(res1, color='orange', label='Storage level')
    plt.axhline(res3, color='orange', ls='--', label='Max Storage')
    plt.plot(res2, color='blue', label='Hydrogen production')
    plt.plot(Demand, color='blue', ls='--', label='Demand')
    plt.legend(loc='best')

    plt.figure(3)
    res1 = ElectricityStored.X
    res2 = ElectricityProd.X
    res3 = ElectricitySold.X
    res4 = res2 - res1 - res3  # Electricity used
    res5 = CapacityBattery.X
    plt.plot(res1, color='orange', label='Battery level')
    plt.axhline(res5, color='orange', ls='--', label='Max battery capacity')
    plt.plot(res2, color='blue', label='Electricity production')
    plt.plot(res4, color='green', label='Electricity used')
    plt.plot(res3, color='red', label='Electricity sold')
    plt.legend(loc='best')


plt.show()
