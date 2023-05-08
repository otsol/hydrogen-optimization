# -*- coding: utf-8 -*-
# Optimization of hydrogen production price
import itertools
# Constraints: Production of hydrogen has to meet demand
# All optimized variables are real numbers >=0


import random

import gurobipy as gp
from gurobipy import GRB
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import csv

results = []
countries =  ["FI", "SE", "DE"] # Countries
prices = ["22"]           # PAP prices # 22 = 2022 Q4 prices, 20 = 2020 Q4 prices
sensScenarios = ["CapexElecDown", "CapexElecUp", "RElecDown", "RElecUp", "EfficiencyElecDown", "EfficiencyElecUp"] # sensitivity scenarios

for country in countries:
    for price in prices:
        for scenario in sensScenarios:
            print("Scenario: BASE " + country + " " + price + " " + scenario)

            #### CREATE MODEL
            m = gp.Model("BASE")

            # number of hours
            nHours = 8784          # FINAL VERSION 8784
            # Set of days
            # hours = range(0, nHours)  # 0 ... 8783
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

            # Storage
            CapacityStorage = m.addVar(vtype = GRB.CONTINUOUS, name="CapacityStorage") # Hydrogen storage capacity (kg)
            HydrogenStored = m.addMVar(nHours, name="HydrogenStored") # Hourly storage level of hydrogen(kg)

            # Supporting variables
            ElectricityProd = m.addMVar(nHours, name="ElectrisityProd") # CapasityWind * CapFactorWind[h] + CapasitySolar * CapFactorSolar[h]

            #### ADD PARAMETERS

            # Demand 
            Demand = np.zeros(nHours)     # hourly demand
            Demand[0:5065] = 2000      # January-June production  
            Demand[5809:nHours] = 2000   # July maintenance break and after full steam. 

            # Electrolyzer
            if scenario == "CapexElecDown":
                CapexElec = 845000 * 0.8     # € / MWe  
                OpexElec = 16900 * 0.8      # € / MWe
                EfficiencyElec = 15.6 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.171   # annuiteettikerroin
            elif scenario == "CapexElecUp":
                CapexElec = 845000 * 1.2     # € / MWe 
                OpexElec = 16900 * 1.2     # € / MWe
                EfficiencyElec = 15.6 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.171   # annuiteettikerroin
            elif scenario == "RElecDown":
                CapexElec = 845000     # € / MWe 
                OpexElec = 16900     # € / MWe
                EfficiencyElec = 15.6 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.148   # annuiteettikerroin
            elif scenario == "RElecUp":
                CapexElec = 845000     # € / MWe 
                OpexElec = 16900     # € / MWe
                EfficiencyElec = 15.6 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.207   # annuiteettikerroin
            elif scenario == "EfficiencyElecDown":
                CapexElec = 845000     # € / MWe 
                OpexElec = 16900     # € / MWe
                EfficiencyElec = 15.6 * 0.8 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.171   # annuiteettikerroin
            elif scenario == "EfficiencyElecUp":
                CapexElec = 845000     # € / MWe 
                OpexElec = 16900     # € / MWe
                EfficiencyElec = 15.6 * 1.2 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.171   # annuiteettikerroin                   
            else:
                CapexElec = 845000     # € / MWe 
                OpexElec = 16900     # € / MWe
                EfficiencyElec = 15.6 # kg H2 / MWHe     
                Pchange = 0.50  # 50% muutos maksimikapasiteetista tunnissa
                RElec = 0.171   # annuiteettikerroin 

            # Wind
            if country == "FI":
                if price == "22":
                    BasePriceWind = 54.6  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceWind = 31.5
                ElecTax = 0.63     # sähkönvero (€ / MWh)
                TransmisFee = 4.0   # sähkönsiirtomaksu (€ / MWh)  
            elif country == "SE":
                if price == "22":
                    BasePriceWind = 72.45  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceWind = 52    
                ElecTax = 0     # sähkönvero (€ / MWh)
                TransmisFee = 0.91   # sähkönsiirtomaksu (€ / MWh)  
            else:
                if price == "22":
                    BasePriceWind = 67.2  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceWind = 57.8       
                ElecTax = 0     # sähkönvero (€ / MWh)
                TransmisFee = 12   # sähkönsiirtomaksu (€ / MWh)  

            CapFactorWind = np.zeros(nHours)  # Tuntikohtainen kapasiteettikerroin
            CapFactorWind[0:5065] = 1
            CapFactorWind[5805:nHours] = 1

            # Solar
            if country == "FI":
                if price == "22":
                    BasePriceSolar = 39.9  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceSolar = 36.8           
            elif country == "SE":
                if price == "22":
                    BasePriceSolar = 57.6  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceSolar = 36.8 
            else:
                if price == "22":
                    BasePriceSolar = 93.45  # PPA pay-as-produced hinta (€ / MWhh)
                else:
                    BasePriceSolar = 51.5 

            CapFactorSolar = np.zeros(nHours)  # Tuntikohtainen kapasiteettikerroin
            CapFactorSolar[0:5065] = 1
            CapFactorSolar[5805:nHours] = 1


            # Storage
            CapexStorage = 80.90  # € / kg 
            OpexStorage = 3.24     # € / kg 
            RStorage = 0.092     # annuiteettikerroin

            # Water
            WaterCost = 0.07 # € / kg H2

            #### ADD CONSTRAINTS

            # Constrain definitions for supporting variables
            m.addConstrs((WindProd[h]
                        == (CapacityWind * CapFactorWind[h]) for h in range(0, nHours)), name="WindProdConstr")

            m.addConstrs((SolarProd[h]
                        == (CapacitySolar * CapFactorSolar[h]) for h in range(0, nHours)), name="SolarProdConstr")

            m.addConstrs((ElectricityProd[h]
                        == (WindProd[h] + SolarProd[h])  for h in range(0, nHours)), name="ElectricityProdConstr")

            # Real world puts limitation on puchased capacity
            m.addConstr(CapacityWind <= 200, name="WindCapacityConstr")

            m.addConstr(CapacitySolar <= 200, name="SolarCapacityConstr")

            # Production and change in storage needs to meet demand
            m.addConstrs((Demand[h]
                        == HydrogenProd[h] + HydrogenStored[h-1] - HydrogenStored[h] for h in range(1, nHours)), name="DemandConstr")

            # There needs to be enough electricity for hydrogen production
            m.addConstrs((HydrogenProd[h]
                        <= ElectricityProd[h] * EfficiencyElec for h in range(0, nHours)), name="ElectricityForProdConstr")

            # Hydrogen production cannot exceed capacity
            m.addConstrs((HydrogenProd[h]
                        <= CapacityElec * EfficiencyElec for h in range(0, nHours)), name="HydrogenProdCapacityConstr")

            # Constraints for hydrogen production
            m.addConstrs((HydrogenProd[h] - HydrogenProd[h-1] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PupConstr")
            m.addConstrs((HydrogenProd[h-1] - HydrogenProd[h] <= (Pchange * CapacityElec * EfficiencyElec) for h in range(1, nHours)), name="PdownConstr")

            # Hydrogen storage cannot exceed capacity. Initial condition = 4000
            m.addConstrs((HydrogenStored[h] <= CapacityStorage for h in range(0, nHours)), name="CapacityStorageConstr")
            m.addConstr((HydrogenStored[0] == 4000), name="StorageInitConditionConstr")


            #### SET OBJECTIVE
            m.setObjective(((CapexElec*RElec + OpexElec)*CapacityElec 
                            + (CapexStorage * RStorage + OpexStorage)*CapacityStorage 
                            + gp.quicksum((BasePriceWind+ElecTax+TransmisFee)*CapFactorWind[h]*CapacityWind for h in range(0,nHours)) 
                            + gp.quicksum((BasePriceSolar+ElecTax+TransmisFee)*CapFactorSolar[h]*CapacitySolar for h in range(0,nHours))
                            + gp.quicksum(HydrogenProd[h]*WaterCost for h in range(0,nHours))
                            ), GRB.MINIMIZE)

            #### OPTIMIZE

            # NonConvex, quadratic equity constraints
            m.Params.NonConvex = 2
            m.optimize()


            #### PLOT
            # m.printAttr("C")
            # plt.figure(1)
            """             for index, v in enumerate(m.getVars()):
                # plt.scatter(index, v.X)
                # plt.title(v.VarName)
                print('%s %g' % (v.VarName, v.X))
            print('Obj : %g' % m.ObjVal) """

            #### APPEND RESULTS
            capacityElec = m.getVarByName("CapacityElec")
            capacitySolar = m.getVarByName("CapacitySolar")
            capacityWind = m.getVarByName("CapacityWind")
            capacityStorage = m.getVarByName("CapacityStorage")
            obj = m.objVal
            x = [country, price, scenario, capacityElec.X, capacitySolar.X, capacityWind.X, capacityStorage.X, obj]
            results.append(x)
            print(results)
                

#### EXPORT TO CSV
with open('sensitivity_base.csv', mode='w', newline='') as output_file:
    # Create a CSV writer
    writer = csv.writer(output_file)

    # Write the header row
    writer.writerow(['Country', 'PAP Year', 'Scenario', 'CapacityElec', 'CapacitySolar', 'CapacityWind', 'CapacityStorage', 'Objective'])

    # Write the variable names and values to the CSV file
    for v in results:
        writer.writerow(v)