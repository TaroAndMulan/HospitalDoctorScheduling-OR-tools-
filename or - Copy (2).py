"""doctor scheduling problem with shift requests."""
from ortools.sat.python import cp_model


def main():



    
    date_type = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    date_start = "Friday"
    date_start_int = 4

    def dt(x):
        return date_type[(4+x)%7]



    # This program tries to find an optimal assignment of doctor to shifts
    # (3 shifts per day, for 7 days), subject to some constraints (see below).
    # Each doctor can request to be assigned to specific shifts.
    # The optimal assignment maximizes the number of fulfilled shift requests.
    num_doctor = 8
    num_shifts = 2
    num_days = 30
    all_doctor = range(num_doctor)
    all_shifts = range(num_shifts)
    all_days = range(num_days)
    shift_requests = [
        [[0,0], [0,  0], [0,  0], [0,  0], [1,  1], [1, 1], [1,  1]],
        [[0,0], [0,  0], [0,  0], [0,  0], [1,  1], [1, 1], [1,  1]],
        [[1,1], [1,  1], [1,  1], [0,  0], [1,  1], [1, 1], [1,  1]],
        [[1,1], [1,  1], [1,  1], [0,  0], [1,  1], [1, 1], [1,  1]],
        [[0,0], [0,  0], [1,  1], [1,  1], [0,  0], [0, 0], [0,  0]],
        [[0,0], [0,  0], [0,  0], [1,  1], [0,  0], [0, 0], [0,  0]],
        [[1,1], [1,  1], [1,  1], [0,  0], [1,  1], [1, 1], [1,  1]],
        [[1,1], [1,  1], [1,  1], [0,  0], [1,  1], [1, 1], [1,  1]],
    ]

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: doctor 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_doctor:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")

    # Each shift is assigned to exactly one doctor in .
    for d in all_days:
        for s in all_shifts:
            model.AddExactlyOne(shifts[(n, d, s)] for n in all_doctor)

    # Each doctor works at most one shift per day.
    for n in all_doctor:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

    # At most 1 consecutive day [EXCLUDE WEEKEND]
    for n in all_doctor:
        for d in all_days:
            if (dt(d)!="Friday" and dt(d)!="Saturday" and dt(d)!="Sunday"):
                if(d<num_days-1):
                    model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d,d+2))
    # WEEKEND RULES
        #FRIDAY = SAT = SUN
    for n in all_doctor:
        for d in all_days:
            if (dt(d)=="Friday" and d<num_days-2):
                model.Add(shifts[(n, d, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d, 1)]==shifts[(n,d+1,0)])
                model.Add(shifts[(n, d+2, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d+2, 1)]==shifts[(n,d+1,0)])
            elif (dt(d)=="Friday" and d<num_days-1):
                model.Add(shifts[(n, d, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d, 1)]==shifts[(n,d+1,0)])
    #AFTERweekend  Sunday != Monday
    
    for n in all_doctor:
        for d in all_days:
            if (dt(d)=="Monday" and d>0):
                model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d-1,d+1))       

 

    


    # Try to distribute the shifts evenly, so that each doctor works
    # min_shifts_per_doctor shifts. If this is not possible, because the total
    # number of shifts is not divisible by the number of doctor, some doctor will
    # be assigned one more shift.
    min_shifts_per_doctor = (num_shifts * num_days) // num_doctor
    if num_shifts * num_days % num_doctor == 0:
        max_shifts_per_doctor = min_shifts_per_doctor
    else:
        max_shifts_per_doctor = min_shifts_per_doctor + 1
    for n in all_doctor:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        model.Add(min_shifts_per_doctor <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_doctor)

   # equal number of weekend (<2 per person)  I check how many sunday
    for n in all_doctor:
        num_weekend = 0
        for d in all_days:
            if(dt(d)=="Sunday"):
                for s in all_shifts:
                    num_weekend += shifts[(n, d, s)]
        model.Add(num_weekend <= 2)
        model.Add(num_weekend>0)

    # sum left = sum rigth
    for n in all_doctor:
        num_ER_worked = 0
        num_Ward_worked = 0
        for d in all_days:
            num_ER_worked += shifts[(n,d,0)]
            num_Ward_worked += shifts[(n,d,1)]
        model.Add(num_ER_worked-num_Ward_worked<=1)
        model.Add(num_ER_worked-num_Ward_worked>=-1)
    # pylint: disable=g-complex-comprehension
    """
    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_doctor
            for d in all_days
            for s in all_shifts
        )
    ) """

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # stat table
    table = [[0 for i in range(num_shifts)] for j in range(num_days)]
    weekendTable = [0 for i in range(num_doctor)]

    if status == cp_model.OPTIMAL:
        print("Solution:")
        for d in all_days:
            """print("Day", d)"""
            for n in all_doctor:
                for s in all_shifts:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        table[d][s] = n
                        if(dt(d)=="Sunday"):
                            weekendTable[n]+=1
                        """
                        if shift_requests[n][d][s] == 1:
                            //print("doctor", n, "works shift", s, "(requested).")
                        else:
                            print("doctor", n, "works shift", s, "(not requested).") 
                        """
        print(
            f"Number of shift requests met = {solver.ObjectiveValue()}",
            f"(out of {num_doctor * min_shifts_per_doctor})",
        )
    else:
        print("No optimal solution found !")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")


    #PRINT RESULT (MANUAL)
    for dd,tt in enumerate(table):
        print(f"day{dd+1}({dt(dd)}): {tt[0]} {tt[1]}")
    grade  = [[0,0] for i in range(num_doctor)]
    for tt in table:
        grade[tt[0]][0]+=1
        grade[tt[1]][1]+=1
    for i in range(num_doctor):
        print(f"doctor{i}: ER:{grade[i][0]} WARD:{grade[i][1]} WEEKEND:{weekendTable[i]} TOTAL:{grade[i][0]+grade[i][1]}")



if __name__ == "__main__":
    main()