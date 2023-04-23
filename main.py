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
import pandas as pd
import csv

#### DOWNLOAD DATA
## Wind download
df = pd.read_excel('wind_FI.xlsx')

# Extract the data from column E
windRaw = df.iloc[:, 4]
# Remove the header row
windRaw = windRaw[0:] 
windRaw = windRaw.astype(float)
# Convert the data to a Python array
windRaw = windRaw.to_numpy()

## Solar download
df = pd.read_excel('solar_FI.xlsx')

# Extract the data from column G
solarRaw = df.iloc[:, 6]
# Remove the header row
solarRaw = solarRaw[0:] 
solarRaw = solarRaw.astype(float)
# Convert the data to a Python array
solarRaw = solarRaw.to_numpy()

# Read the xlsx file
df = pd.read_excel('electricity_price_FI.xlsx')

# Extract the data from column E
priceRaw = df.iloc[:, 4]
# Remove the header row
priceRaw = priceRaw[0:] 
priceRaw = priceRaw.astype(float)
# Convert the data to a Python array
priceRaw = priceRaw.to_numpy()

#### CREATE MODEL
m = gp.Model("PAP-FI")

# number of hours
nHours = 8760          # FINAL VERSION 8760
# Set of days
# hours = range(0, nHours)  # 0 ... 8759
hours = np.arange(0, nHours)

#### ADD DECISION VARIABLES

# Electrolyzer
CapacityElec = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityElec")
HydrogenProd = m.addMVar(nHours, name="HydrogenProd") # Hourly hydrogen production (kg)

# Wind
CapacityWind = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityWind") # Ostettu tuulen tuotantokapasiteetti (MW) PAP
WindProd = m.addMVar(nHours, name="WindProd") # multiply helper variable

# Solar
CapacitySolar = m.addVar(vtype = GRB.CONTINUOUS, name="CapacitySolar") # Ostettu aurikovoima tuotantokapasiteetti (MW) PAP
SolarProd = m.addMVar(nHours, name="SolarProd") # multiply helper variable

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
Demand[0:5041] = 2000      # January-June production  
Demand[5785:nHours] = 2000   # July maintenance break and after full steam. 

# Electrolyzer
CapexElec = 845000     # € / MWe 
OpexElec = 16900      # € / MWe
EfficiencyElec = 15.6 # kg H2 / MWHe     
Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
RElec = 0.171   # annuiteettikerroin

# Wind
PapPriceWind = 52  # PPA pay-as-produced hinta (€ / MWhh) 
ElecTax = 0.63     # sähkönvero (€ / MWh)
TransmisFee = 4.0   # sähkönsiirtomaksu (€ / MWh) 
CapFactorWind = []  # Tuntikohtainen kapasiteettikerroin
for row in windRaw:
    CapFactorWind.append(row)

# Solar
PapPriceSolar = 38  # PPA pay-as-produced hinta (€ / MWh) 
CapFactorSolar = []  # Tuntikohtainen kapasiteettikerroin
for row in solarRaw:
    CapFactorSolar.append(row)

# Battery
DepthOfDischarge = 0.8
CapexBattery = 378798
OpexBattery = 7576
ChargeEfficiency = 0.93
ChargePowerPerc = 0.43  # Charge rate as a ratio of max capacity
RBattery = 0.147        # annuiteettikerroin

# Storage
CapexStorage = 80.90  # € / kg 
OpexStorage = 3.24     # € / kg 
RStorage = 0.092     # annuiteettikerroin

# Grid
GridPrice = []  # Tuntikohtainen kapasiteettikerroin
for row in priceRaw:
    GridPrice.append(row)

# WACC
Wacc = 0.078

#### ADD CONSTRAINTS

# Constrain definitions for supporting variables
m.addConstrs((WindProd[h]
              == (CapacityWind * CapFactorWind[h]) for h in range(0, nHours)), name="WindProdConstr")

m.addConstrs((SolarProd[h]
              == (CapacitySolar * CapFactorSolar[h]) for h in range(0, nHours)), name="SolarProdConstr")

m.addConstrs((ElectricityProd[h]
              == (WindProd[h] + SolarProd[h])  for h in range(0, nHours)), name="ElectricityProdConstr")

# Real world puts limitation on puchased capacity
m.addConstr(CapacityWind <= 1000, name="WindCapacityConstr")

m.addConstr(CapacitySolar <= 1000, name="SolarCapacityConstr")

# Production and change in storage needs to meet demand
m.addConstrs((Demand[h]
              == (HydrogenProd[h] + HydrogenStored[h-1] - HydrogenStored[h]) for h in range(1, nHours)), name="DemandConstr")

# July maintenance break PITÄÄ ANTAA VÄHINTÄÄN PARI TUNTIA AIKAA AJAA TAKAISIN TUOTANTO YLÖS!!
m.addConstrs((HydrogenProd[h]
              == 0 for h in range(5041, 5782)), name="MaintBreakConstr") 

# There needs to be enough electricity for hydrogen production
m.addConstrs((HydrogenProd[h]
              == (ElectricityProd[h] - ElectricitySold[h] + ChargeEfficiency*(ElectricityStored[h-1] - ElectricityStored[h])) * EfficiencyElec for h in range(0, nHours)), name="ElectricityForProdConstr")

# Hydrogen production cannot exceed capacity
m.addConstrs((HydrogenProd[h]
              <= CapacityElec * EfficiencyElec for h in range(0, nHours)), name="HydrogenProdCapacityConstr")

# Constraints for hydrogen production
m.addConstrs((HydrogenProd[h] - HydrogenProd[h-1] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PupConstr")
m.addConstrs((HydrogenProd[h-1] - HydrogenProd[h] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PdownConstr")

# Hydrogen storage cannot exceed capacity. Initial condition = 0
m.addConstrs((HydrogenStored[h] <= CapacityStorage for h in range(1, nHours)), name="CapacityStorageConstr")
m.addConstr((HydrogenStored[0] == 0), name="StorageInitConditionConstr")

# Electricity balance
m.addConstrs((ElectricityProd[h] - HydrogenProd[h] * (1 / EfficiencyElec) - ElectricitySold[h] + (ElectricityStored[h-1] - ElectricityStored[h])*(1/ChargeEfficiency) == 0 for h in range(0, nHours)), name="ElectricityBalanceConstr")

# Battery constraints
m.addConstr((ElectricityStored[0] == 0), name="BatteryInitConditionConstr")  # Battery starts empty
m.addConstrs((ElectricityStored[h] <= CapacityBattery*DepthOfDischarge for h in range(0, nHours)), name="CapacityBatteryConstr")  # Max battery level 80%
m.addConstrs((ElectricityStored[h]-ElectricityStored[h-1] <= ChargePowerPerc*CapacityBattery*ChargeEfficiency for h in range(1, nHours)), name="BchangeConstr")
m.addConstrs((ElectricityStored[h-1]-ElectricityStored[h] <= ChargePowerPerc*CapacityBattery*ChargeEfficiency for h in range(1, nHours)), name="BchangeConstr")

#### SET OBJECTIVE
m.setObjective(((CapexElec*RElec + OpexElec)*CapacityElec 
                + (CapexStorage * RStorage + OpexStorage)*CapacityStorage 
                + (CapexBattery*RBattery + OpexBattery)*CapacityBattery
                + (CapacitySolar*PapPriceSolar + CapacityWind*PapPriceWind)*7*24*Wacc  
                + gp.quicksum((PapPriceWind+ElecTax+TransmisFee)*CapFactorWind[h]*CapacityWind for h in range(0,nHours)) 
                + gp.quicksum((PapPriceSolar+ElecTax+TransmisFee)*CapFactorSolar[h]*CapacitySolar for h in range(0,nHours))
                - gp.quicksum((GridPrice[h]+ElecTax+TransmisFee)*ElectricitySold[h] for h in range(0,nHours))
                ), GRB.MINIMIZE)

#### OPTIMIZE

# NonConvex, quadratic equity constraints
m.Params.NonConvex = 2
m.optimize()


#### PLOT
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
    res2 = SolarProd.X
    res3 = ElectricitySold.X
    res6 = WindProd.X
    res4 = res2 + res6 - res1 - res3  # Electricity used
    res5 = CapacityBattery.X
    
    plt.plot(res1, color='orange', label='Battery level')
    plt.axhline(res5, color='orange', ls='--', label='Max battery capacity')
    plt.plot(res2, color='blue', label='Solar production')
    plt.plot(res4, color='green', label='Electricity used')
    plt.plot(res3, color='red', label='Electricity sold')
    plt.plot(res6, color='black', label='Wind production')
    plt.legend(loc='best')
    


plt.show()

#### EXPORT TO XLSX
with open('output.csv', mode='w', newline='') as output_file:
    # Create a CSV writer
    writer = csv.writer(output_file)

    # Write the header row
    writer.writerow(['Variable', 'Value'])

    # Write the variable names and values to the CSV file
    for v in m.getVars():
        writer.writerow([v.varName, v.x])

    # Write the objective value to the CSV file
    writer.writerow(['Objective', m.objVal])