"""doctor scheduling problem with shift requests."""
from ortools.sat.python import cp_model
from termcolor import colored, cprint


def main():

    #INIT variable
    date_type = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    date_start = "Friday"
    date_start_int = 4

    doctor_name = ["กร","กรรณ","กาย","ทาโร่","มู่หลาน","ซิมบ่า","นาร่า","เสือ","---"]

    def dt(x):
        return date_type[(date_start_int+x)%7]

    num_doctor = 8
    num_shifts = 2
    num_days = 31
    all_doctor = range(num_doctor)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    #REAL DATE / no OFFSET
    all_exception = [
        [4,11,15,16,17,18],
        [15,16,17],
        [23,24,26],
        [23,24],
        [],
        [],
        [],
        [],
    ]
    #REAL DATE/ no OFFSET
    all_outside = [
        [14,1],
        [5,0]
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
            blocked=False
            for o in all_outside:
                if(o[0]-1==d and o[1]==s):
                    blocked=True
            if(not blocked):
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

 
    #EXCEPTION FROM DOCTOR
    #d-1 because day in exception start with 1 not 0 (OFFSET)
    for n in all_doctor:
        for d in all_exception[n]:
            model.Add(shifts[(n,d-1,0)]==0)
            model.Add(shifts[(n,d-1,1)]==0)

    #EXCEPTION FROM OUTSIDE DOCTOR
    for o in all_outside:
       for n in all_doctor:
            model.Add(shifts[(n,o[0]-1,o[1])]==0)

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
    table = [[-1 for i in range(num_shifts)] for j in range(num_days)]
    weekendTable = [0 for i in range(num_doctor)]
    exceptionTable = [0 for i in range(num_doctor)]

    if status == cp_model.OPTIMAL:
        for d in all_days:
            for n in all_doctor:
                for s in all_shifts:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        #fill stat table
                        table[d][s] = n
                        #fill wweekend table
                        if(dt(d)=="Sunday"):
                            weekendTable[n]+=1
                        #fill exception table (plus 1 for offset)
                        if(d+1 in all_exception[n]):
                            exceptionTable[n]+=1

    else:
        print("No optimal solution found !")

    #PRINT RESULT (MANUAL)
    cprint("-------------------------","red")
    #print solved scedules
    for dd,tt in enumerate(table):
        if (dt(dd)!="Saturday" and dt(dd)!="Sunday"):
            print(f'{f"day{dd+1} ({dt(dd)})":20} {doctor_name[tt[0]]} {doctor_name[tt[1]]}')
        if (dt(dd)=="Saturday" or dt(dd)=="Sunday"):
            cprint(f'{f"day{dd+1} ({dt(dd)})":20} {doctor_name[tt[0]]} {doctor_name[tt[1]]}',"green")
        cprint("-------------------------","red")

    grade  = [[0,0,0,0] for i in range(num_doctor)]

    #calculate ER and Ward normal
    for dd,tt in enumerate(table):
        if(dt(dd)=="Saturday" or dt(dd)=="Sunday"):
            if(tt[0]!=-1):
                grade[tt[0]][2]+=1
            if(tt[1]!=-1):
                grade[tt[1]][3]+=1
        else:
            if(tt[0]!=-1):
                grade[tt[0]][0]+=1
            if(tt[1]!=-1):
                grade[tt[1]][1]+=1     

    # PRINT STATISTIC       
    for i in range(num_doctor):
        print(f"doctor {i}: (NORMAL)  ER:{grade[i][0]} WARD:{grade[i][1]}  TOTAL:{grade[i][0]+grade[i][1]}")
        print(f"          (WEEKEND) ER:{grade[i][2]} WARD:{grade[i][3]}  TOTAL:{grade[i][2]+grade[i][3]} ")
        print(f"          TOTAL: {sum(grade[i])}")
        cprint("-------------------------","red")

    #EXCEPTION_FAIL:{exceptionTable[i]}
        
    #OUTPUT DATA


if __name__ == "__main__":
    main()