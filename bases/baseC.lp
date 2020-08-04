#const bound = 100.
time(1..bound).

action(up).
action(down).
action(left).
action(right).
action(wait).

delta(right,X,Y,X+1,Y) :- rangeX(X), rangeY(Y).
delta(left,X,Y,X-1,Y) :- rangeX(X), rangeY(Y).
delta(up,X,Y,X,Y+1) :- rangeX(X), rangeY(Y).
delta(down,X,Y,X,Y-1) :- rangeX(X), rangeY(Y).
delta(wait,X,Y,X,Y) :- rangeX(X),rangeY(Y).

at(R,X,Y,T) :- exec(R,A,T-1),on(R,Xp,Yp,T-1),delta(A,Xp,Yp,X,Y).

:- at(R1,X1+1,Y1,T-1), at(R2,X1,Y1,T-1), at(R1,X1,Y1,T), at(R2,X1+1,Y1,T),R1!=R2.
:- at(R1,X1,Y1+1,T-1), at(R2,X1,Y1,T-1), at(R1,X1,Y1,T), at(R2,X1,Y1+1,T),R1!=R2.

1 {exec(R,A,T-1) : action(A)} 1 :- robot(R), time(T).

:- at(R,X,Y,T), not rangeX(X).
:- at(R,X,Y,T), not rangeY(Y).
:- at(R1,X,Y,T),at(R2,X,Y,T),R1<R2.
:- at(R,X,Y,T),obstacle(X,Y). %no hay robots encima de obstaculos


% one action executed at each time step
1 {exec(R,A,T-1) : action(A)} 1 :- robot(R), time(T).

penalty(R,T,1) :- time(T), dijkstra(R,Tp), T>Tp, at_goal_back(R,T-1).

:- at(R,X,Y,T),obstacle(X,Y). %no hay robots encima de obstaculos


at_goal(R,T) :- at(R,X,Y,T), goal(R,X,Y).
:- robot(R), not at_goal(R,bound).

at_goal_back(R,bound) :- robot(R).
at_goal_back(R,T-1) :- at_goal_back(R,T),exec(R,wait,T-1).


#maximize {P,R,T : penalty(R,T,P)}.
#show at/4.

