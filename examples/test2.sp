R1 in out 10
R2 out n4 10
C1 out 0 1e-12
C2 n4 0 1e-12
L1 n5 n4 1e-12
I1 n5 0 PWL 0 0 5e-11 0.001 1e-10 0
V1 in 0 DC 1
.probe out
