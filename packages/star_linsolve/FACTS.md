# Published values the tests of star_linsolve may cite (checked by the reviewer against the computation)

1. Hilbert matrix of order 3, H = ((1, 1/2, 1/3), (1/2, 1/3, 1/4), (1/3, 1/4, 1/5)) (MathWorld, "Hilbert Matrix"; Choi, "Tricks or treats with the Hilbert matrix", American
   Mathematical Monthly 90, 1983): determinant 1/2160, inverse ((9, -36, 30), (-36, 192, -180), (30, -180, 180)); the Hilbert matrix of order 4 has determinant 1/6048000.
   Multiplied by 60, H has the integer entries A = ((60, 30, 20), (30, 20, 15), (20, 15, 12)): det(A) == 100.0 exactly (60^3 / 2160);
   inverse(A) == ((0.15, -0.6, 0.5), (-0.6, 3.2, -3.0), (0.5, -3.0, 3.0)) exactly (the published inverse divided by 60); solve(A, [110, 65, 47]) == (1.0, 1.0, 1.0) exactly (row sums).
   With the float entries 1/(i + j + 1) the matrix is not exactly H: det is 1/2160 within 1e-13 relative and the inverse is the published one within 1e-12 relative.

Values derivable by hand (write the derivation in a comment):
- det(a) returns a float; solve(a, b) returns a tuple of n floats; inverse(a) returns a tuple of n tuples of n floats; a is a list or tuple of rows (lists or tuples);
- 1 x 1: det([[3]]) == 3.0; solve([[5]], [10]) == (2.0,); inverse([[4]]) == ((0.25,),);
- 2 x 2: det([[1, 2], [3, 4]]) == -2.0; inverse([[1, 2], [3, 4]]) == ((-2.0, 1.0), (1.5, -0.5)); inverse([[4, 7], [2, 6]]) == ((0.6, -0.7), (-0.2, 0.4)) [1/10 of ((6, -7), (-2, 4))];
  solve([[2, 1], [1, 3]], [3, 5]) == (0.8, 1.4) [det 5: x = (9 - 5)/5, y = (10 - 3)/5];
- a zero on the diagonal needs a row exchange, which changes the sign of the determinant: det([[0, 1], [1, 0]]) == -1.0; det([[0, 2], [3, 0]]) == -6.0; solve([[0, 2], [3, 0]], [4, 9]) == (3.0, 2.0);
- triangular and diagonal: det([[2, 0, 0], [0, 3, 0], [0, 0, 4]]) == 24.0; the determinant of a triangular matrix is the product of its diagonal;
- 3 x 3: det([[1, 2, 3], [4, 5, 6], [7, 8, 10]]) == -3.0; solve of that matrix with [6, 15, 25] == (1.0, 1.0, 1.0); its inverse is ((-2/3, -4/3, 1), (-2/3, 11/3, -2), (1, -2, 1));
  the second-difference matrix T = ((2, -1, 0), (-1, 2, -1), (0, -1, 2)) has det 4.0 and inverse ((0.75, 0.5, 0.25), (0.5, 1.0, 0.5), (0.25, 0.5, 0.75)); solve(T, [1, 0, 1]) == (1.0, 1.0, 1.0);
- singular exactly: det([[1, 2], [2, 4]]) == 0.0; det([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == 0.0; det([[0.1, 0.2], [0.3, 0.6]]) == 0.0 exactly (the floats 0.2 and 0.6 are exactly twice the
  floats 0.1 and 0.3); solve and inverse refuse these ("singular");
- nearly singular is solved, not refused: with e = 2**-52, det([[1, 1], [1, 1 + e]]) == e exactly; solve([[1, 1], [1, 1 + e]], [2, 2]) == (2.0, 0.0);
  solve([[1, 1], [1, 1 + e]], [2, 2 + 2 * e]) == (0.0, 2.0) [x + y = 2 and e y = 2 e]; inverse([[1, 1], [1, 1 + e]]) == ((2**52 + 1, -2**52), (-2**52, 2**52)) exactly;
- identities: the identity of order 20 has det 1.0 and is its own inverse exactly; det of a matrix with two equal rows is 0.0; exchanging two rows changes the sign of det exactly;
  multiplying one row by 2 doubles det exactly; det of the transpose is the same float; inverse(inverse(a)) is a within 1e-12 relative for a well-conditioned a;
  a times solve(a, b) is b within 1e-12 for well-conditioned a (the residual is not exactly zero: each component is rounded);
- scale: det([[1e100, 0], [0, 1e100]]) == 1e200; det([[1e-200, 0], [0, 1e-200]]) == 0.0 (1e-400 underflows: a determinant of 0.0 is not a proof of singularity), and yet
  inverse([[1e-200, 0], [0, 1e-200]]) is ((1e200, 0.0), (0.0, 1e200)) within 1e-15 relative, the matrix being regular.

Limits (state them): MAX_SIZE == 20, BIG == 1e100. Refusals (ValueError):
- a: not a list or tuple (a string, None, a number, a set), empty, 21 rows ("1 to 20 rows"); a row that is not a list or tuple, or of the wrong length ("must be square");
  an entry that is a bool, a string, None, a complex, nan, inf, or beyond 1e100 (1.0000001e100; 1e100 itself is accepted);
- b: not a list or tuple, a wrong number of values ("b must be a list or tuple of n numbers", with n written out), an entry as above ("b must hold finite real numbers");
- solve and inverse: a singular matrix ("the matrix is singular"); det of a singular matrix is 0.0 and is not refused;
- a result too large for a float ("too large"): det of the diagonal matrix of order 4 with 1e100 on the diagonal (1e400); solve([[1e-300]], [1e100]) (1e400); inverse([[1e-200, 0], [0, 1e-200]]) is
  accepted (1e200), inverse([[5e-324]]) is refused (2e323).
