# Thayang hospital Doctor Scheduler

* This python script provides a monthly optimal shift assignment for doctors in the hospital.
* Near the end of each month, doctors submit their availability for the upcoming month, The script then generates an optimal monthly schedules, considering both doctor preferences and hospital requirements.
* Prior to implementation, it took 2-3 days for hospital staff to finalize a schedule that contained no major conflict. My program solves this scheduling problem within SECONDS and WITHOUT any conflict.
* Technical details:  Hospital requirements and doctor availability are translated into mathematics equations (constraints), then solved using a constraint programming solver (ORTOOLS). \
* See pdf file for more detail