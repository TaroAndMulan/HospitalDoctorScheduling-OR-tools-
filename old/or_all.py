"""doctor scheduling problem with shift requests."""
from ortools.sat.python import cp_model
from termcolor import cprint


def main():

    #INIT variable
    date_type = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    date_start = "Monday"
    date_start_int = 0

    doctor_name = {1:"เจน",2:"นาวา",3:"จี้",4:"อู๋",5:"เกมส์",6:"เมก",7:"นาร่า",8:"เสือ",-1:"---"}

    def dayTodate(x):
        return date_type[(date_start_int+x-1)%7]

    num_doctor = 8
    num_shifts = 2
    num_days = 31
    all_doctors = range(1,num_doctor+1)
    all_shifts = range(num_shifts)
    all_days = range(1,num_days+1)
    max_week_offset = 2
    min_week_offset = 0    #negative
    # EXCEPTION INSIDE DOCTOR
    all_exception = {
        1:[19,20,21],
        2:[],
        3:[],
        4:[],
        5:[1,8,15,22,23,24,29],
        6:[2,13,19,20,21],
        7:[],
        8:[]}

    #EXCEPTION OUTSIDE DOCTOR
    all_outside = [
        [2,1],
        [10,1],
        [30,0],
        [31,0]
    ]

    all_holidays = [
        1
    ]
   
   # calculate weekend+sat+sun
    num_holidayplusweekend = len(all_holidays)
    for d in all_days:
        if dayTodate(d)=="Saturday" or dayTodate(d)=="Sunday":
            num_holidayplusweekend+=1

    # Creates the model.
    model = cp_model.CpModel()

    # CONSTRAINTS
     #region


    # Creates shift variables.
    # shifts[(n, d, s)]: doctor 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_doctors:
        shifts[n] = model.NewIntVar(1, 35, "avg_n{n}")

        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")
    # Each shift is assigned to exactly one doctor in .
    # except occupy by outside doctor
    for d in all_days:
        for s in all_shifts:
            blocked=False
            for o in all_outside:
                if(o[0]==d and o[1]==s):
                    blocked=True
            if(not blocked):
                model.AddExactlyOne(shifts[(n, d, s)] for n in all_doctors)

    # Each doctor works at most one shift per day.
    for n in all_doctors:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)
    """
    # At most 2 consecutive day [EXCLUDE WEEKEND]
    for n in all_doctors:
        for d in all_days:
            if (dayTodate(d)!="Friday" and dayTodate(d)!="Saturday" and dayTodate(d)!="Sunday" and dayTodate(d)!="Thursday" ):
                if(d<num_days-1):
                    model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d,d+3))
                elif(d<num_days):
                    model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d,d+2))
            if(dayTodate(d)=="Thursday"):
                if(d<num_days):
                    model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d,d+2))
    """

    # At most 1 consecutive day [EXCLUDE WEEKEND]
    for n in all_doctors:
        for d in all_days:
            if (dayTodate(d)!="Friday" and dayTodate(d)!="Saturday" and dayTodate(d)!="Sunday"):
                if(d<num_days):
                    model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d,d+2))
    
    # WEEKEND RULES
                    

        #FRIDAY = SAT = SUN
    for n in all_doctors:
        for d in all_days:
            if (dayTodate(d)=="Friday" and d<num_days-1):
                model.Add(shifts[(n, d, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d, 1)]==shifts[(n,d+1,0)])
                model.Add(shifts[(n, d+2, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d+2, 1)]==shifts[(n,d+1,0)])
            elif (dayTodate(d)=="Friday" and d<num_days):
                model.Add(shifts[(n, d, 0)]==shifts[(n,d+1,1)])
                model.Add(shifts[(n, d, 1)]==shifts[(n,d+1,0)])
    #AFTERweekend  Sunday != Monday
    
    for n in all_doctors:
        for d in all_days:
            if (dayTodate(d)=="Monday" and d>1):
                model.AddAtMostOne(shifts[(n, x, s)] for s in all_shifts for x in range(d-1,d+1))       

 
    #EXCEPTION FROM INSIDE DOCTOR
    for n in all_doctors:
        for d in all_exception[n]:
            model.Add(shifts[(n,d,0)]==0)
            model.Add(shifts[(n,d,1)]==0)

    #EXCEPTION FROM OUTSIDE DOCTOR
    for o in all_outside:
       for n in all_doctors:
            model.Add(shifts[(n,o[0],o[1])]==0)

    # Try to distribute the shifts evenly
            
    min_shifts_per_doctor = ((num_shifts * num_days)-len(all_outside)) // num_doctor
    if ((num_shifts * num_days)-len(all_outside)) % num_doctor == 0:
        max_shifts_per_doctor = min_shifts_per_doctor
    else:
        max_shifts_per_doctor = min_shifts_per_doctor + 1
    for n in all_doctors:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        model.Add(min_shifts_per_doctor <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_doctor)

   # equal number of weekend+holiday works
    for n in all_doctors:
        num_weekend = 0
        for d in all_days:
            if(dayTodate(d)=="Sunday" or dayTodate(d)=="Saturday" or d in all_holidays):
                for s in all_shifts:
                    num_weekend += shifts[(n, d, s)]
        model.Add(num_weekend <= (num_holidayplusweekend // num_doctor)+max_week_offset)
        model.Add(num_weekend>= (num_holidayplusweekend // num_doctor)-min_week_offset)

    # sum left = sum right
    for n in all_doctors:
        num_ER_worked = 0
        num_Ward_worked = 0
        for d in all_days:
            num_ER_worked += shifts[(n,d,0)]
            num_Ward_worked += shifts[(n,d,1)]
        model.Add(num_ER_worked-num_Ward_worked<=1)
        model.Add(num_ER_worked-num_Ward_worked>=-1)
    #endregion

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 2
    solver.parameters.enumerate_all_solutions = True

    solution = {i:{} for i in range(0,4000)}

    class doctorsPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions."""

        def __init__(self, shifts, num_doctor, num_days, num_shifts, limit, solution):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._num_doctor = num_doctor
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solution_count = 0
            self._solution_limit = limit
            self._max = 0
            self._schedule = {j:[-1 for i in all_shifts] for j in all_days}
            self._solution = solution

        def on_solution_callback(self):
            self._solution_count += 1

            schedule = {j:[-1 for i in all_shifts] for j in all_days}
            countSundayTable = {n:0 for n in all_doctors}
            exceptionViolateTable = {n:0 for n in all_doctors}

            for d in all_days:
                for n in all_doctors:
                    for s in all_shifts:
                        if self.Value(self._shifts[(n, d, s)]):
                            #fill stat table
                            schedule[d][s] = n
                            self._schedule[d][s]=n
                            #fill wweekend table
                            if(dayTodate(d)=="Sunday"):
                                countSundayTable[n]+=1
                            #fill exception table (plus 1 for offset)
                            if(d in all_exception[n]):
                                exceptionViolateTable[n]+=1
            

            #print interval avg
            avg_per_doc = {}
            for n in all_doctors:
                avg_per_doc[n]=0
                last_day = 0
                count = 0
                for d in all_days:
                    for s in all_shifts:
                        if(self.Value(self._shifts[(n,d,s)])):
                            if(last_day!=0):
                                avg_per_doc[n]+= d-last_day
                                last_day=d
                                count+=1
                            if(last_day==0):
                                last_day=d
                avg_per_doc[n] = avg_per_doc[n]/count
            avg = sum(avg_per_doc[c] for c in all_doctors)/len(all_doctors)

            for key in self._shifts:
                self._solution[self._solution_count][key] = self.Value(self._shifts[key])
            
            if(avg>self._max):
                self._max = avg
                self._solution["max"] = self._solution_count

            if self._solution_count >= self._solution_limit:
                print(f"Stop search after {self._solution_limit} solutions")
                self.StopSearch()

        def solution_count(self):
            return self._solution_count

    # Display the first five solutions.
    solution_limit = 100
    solution_printer = doctorsPartialSolutionPrinter(
        shifts, num_doctor, num_days, num_shifts, solution_limit,solution
    )



    solver.Solve(model, solution_printer)


    def print_select_solution(shifts_array):
        #shifts=solution[solution["max"]]
        #print("max",solution["max"])
        #print(solution)
        #print(shifts)
        print("-----------------------PRINT SELECT_SOLUTION-------------------------------")
        schedule = {j:[-1 for i in all_shifts] for j in all_days}
        countSundayTable = {n:0 for n in all_doctors}
        exceptionViolateTable = {n:0 for n in all_doctors}
        for d in all_days:
            for n in all_doctors:
                for s in all_shifts:
                    if shifts_array[(n, d, s)]:
                        #fill stat table
                        schedule[d][s] = n
                                #fill wweekend table
                        if(dayTodate(d)=="Sunday"):
                            countSundayTable[n]+=1
                        #fill exception table (plus 1 for offset)
                        if(d in all_exception[n]):
                            exceptionViolateTable[n]+=1
                
        #PRINT RESULT (MANUAL)
        cprint("-------------------------","red")
        #print interval avg
        avg_per_doc = {}
        for n in all_doctors:
            avg_per_doc[n]=0
            last_day = 0
            count = 0
            for d in all_days:
                for s in all_shifts:
                    if(shifts_array[(n,d,s)]):
                        if(last_day!=0):
                            avg_per_doc[n]+= d-last_day
                            last_day=d
                            count+=1
                        if(last_day==0):
                            last_day=d
            avg_per_doc[n] = avg_per_doc[n]/count
        avg = sum(avg_per_doc[c] for c in all_doctors)/len(all_doctors)
        print([avg_per_doc[c] for c in all_doctors])
        print("avg_interval_total: ",avg)
    

        #print solved scedules
        for d in schedule:
            if (dayTodate(d)!="Saturday" and dayTodate(d)!="Sunday" and d not in all_holidays):
                print(f'{f"day{d} ({dayTodate(d)})":20} {doctor_name[schedule[d][0]]} {doctor_name[schedule[d][1]]}')
            if (dayTodate(d)=="Saturday" or dayTodate(d)=="Sunday" or d in all_holidays):
                cprint(f'{f"day{d} ({dayTodate(d)})":20} {doctor_name[schedule[d][0]]} {doctor_name[schedule[d][1]]}',"green")
            cprint("-------------------------","red")
        stat_table  = {n:[0,0,0,0] for n in all_doctors}

        #calculate ER and Ward normal
        for d in schedule:
            if(dayTodate(d)=="Saturday" or dayTodate(d)=="Sunday" or d in all_holidays):
                if(schedule[d][0]!=-1):
                    stat_table[schedule[d][0]][2]+=1
                if(schedule[d][1]!=-1):
                    stat_table[schedule[d][1]][3]+=1
            else:
                if(schedule[d][0]!=-1):
                    stat_table[schedule[d][0]][0]+=1
                if(schedule[d][1]!=-1):
                    stat_table[schedule[d][1]][1]+=1   
                        

        # PRINT STATISTIC
        
                
        for n in all_doctors:
            print(f" {doctor_name[n]}: (NORMAL)  ER:{stat_table[n][0]} WARD:{stat_table[n][1]}  TOTAL:{stat_table[n][0]+stat_table[n][1]}")
            print(f"          (WEEKEND) ER:{stat_table[n][2]} WARD:{stat_table[n][3]}  TOTAL:{stat_table[n][2]+stat_table[n][3]} ")
            print(f"          TOTAL: {sum(stat_table[n])}")
            print(f"avg_day_interval: {avg_per_doc[n]}")
            cprint("-------------------------","red")     
    
    print_select_solution(solution[solution["max"]])
# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!
# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!
# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!# BEST SOLUTION !!!!!!!!!!
    # BEST SOLUTION !!!!!!!!!!
 
    #  Statistics.
    # print("\nStatistics")
    # print(f"  - conflicts      : {solver.NumConflicts()}")
    # print(f"  - branches       : {solver.NumBranches()}")
    # print(f"  - wall time      : {solver.WallTime()} s")
    # print(f"  - solutions found: {solution_printer.solution_count()}")


if __name__ == "__main__":
    main()