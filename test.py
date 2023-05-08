import gurobipy as gp
from gurobipy import GRB
import csv
results = []
for i in range(6):
    # Create a new model
    m = gp . Model (" mip1 ")
    # Create variables
    
    x = m . addVar ( vtype = GRB . BINARY , name ="x")
    y = m . addVar ( vtype = GRB . BINARY , name ="y")
    z = m . addVar ( vtype = GRB . BINARY , name ="z")
    # Set objective
    m . setObjective ( x + y + 2 * z , GRB . MAXIMIZE )
    # Add constraint : x + 2 y + 3 z <= 4
    
    m . addConstr ( x + i * y + 3 * z <= 4 , "c0")
    # Add constraint : x + y >= 1
    m . addConstr ( x + y >= 1 , "c1")
    # Optimize model
    m . optimize ()
    x = m.getVarByName("x") 
    obj = m.objVal
    x = [x.Varname, x.X, obj]
    """ for v in m . getVarByName ("x"):
        x = [v.Varname,v.X]
        #print ('%s %g' % ( v . VarName , v . X ))
        #print ('Obj : %g' % m . ObjVal ) """

    print(x)
    results.append(x)
print(results)
with open('test.csv', mode='w', newline='') as output_file:
    # Create a CSV writer
    writer = csv.writer(output_file)

    # Write the header row
    writer.writerow(['Variable', 'Value','Objective'])

    # Write the variable names and values to the CSV file
    for v in results:
        writer.writerow(v)

    # Write the objective value to the CSV file
    #