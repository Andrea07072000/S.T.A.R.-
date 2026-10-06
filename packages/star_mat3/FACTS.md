# Values the tests of star_mat3 may cite (checked by the reviewer against the computation)

There is NO published numerical example for these definitions: do not call any number published.

Values derivable by hand (write the derivation in a comment; exact unless a tolerance is given):
- A = [[2, 0, 1], [1, 3, 2], [1, 0, 1]]: determinant(A) == 3.0 (expanding along the second column: 3 * (2*1 - 1*1));
  inverse(A) == ((1, 0, -1), (1/3, 1/3, -1), (-1, 0, 2)) exactly as floats (each entry is the correctly rounded quotient);
  matvec(A, (1, 2, 3)) == (5.0, 13.0, 4.0); matvec(transpose(A), (1, 2, 3)) == (7.0, 6.0, 8.0);
  matmul(A, inverse(A)) is the identity within 1e-15; transpose(A) == ((2, 1, 1), (0, 3, 0), (1, 2, 1));
- identity() == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)); determinant(identity()) == 1.0; inverse(identity()) == identity();
  matmul(identity(), A) == A and matmul(A, identity()) == A as tuples of floats; matvec(identity(), v) == v;
- diagonal matrices: determinant(diag(2, 3, 4)) == 24.0; inverse(diag(4, 2, 1)) == diag(0.25, 0.5, 1.0); a matrix with two equal rows has determinant 0.0 exactly;
  swapping two rows changes the sign of the determinant exactly; determinant(transpose(M)) == determinant(M) exactly;
  multiplying one row by 7 multiplies the determinant by 7 (exactly, for small integers);
- products: matmul is not commutative: with B = [[0, 1, 0], [0, 0, 1], [1, 0, 0]] (a cyclic permutation), matmul(A, B) == ((1, 2, 0), (2, 1, 3), (1, 1, 0)) and
  matmul(B, A) == ((1, 3, 2), (1, 0, 1), (2, 0, 1)); transpose(matmul(A, B)) == matmul(transpose(B), transpose(A)); matmul(A, B) applied to v equals A applied to (B applied to v);
  determinant(matmul(A, B)) == determinant(A) * determinant(B) (B has determinant +1);
- rotations: R = [[c, s, 0], [-s, c, 0], [0, 0, 1]] with c = cos(0.3), s = sin(0.3) is a rotation: is_rotation(R) is True, determinant(R) == 1 within 1e-15,
  inverse(R) equals transpose(R) within 1e-15, and matvec(transpose(R), matvec(R, v)) returns v within 1e-15; B above is a rotation too (is_rotation(B) True);
  a reflection is NOT a rotation: is_rotation(diag(1, 1, -1)) is False (orthonormal, determinant -1); A is not (is_rotation(A) False); 2 * identity is not;
  a rotation perturbed by 1e-9 in one entry fails with the default tolerance 1e-12 and passes with tol = 1e-6;
- exactness: the determinant and the inverse are computed in exact rational arithmetic and rounded once, so
  determinant([[1e15 + 1, 1e15], [...]]) style cancellations are exact: determinant(((1e8 + 1, 1e8, 0), (1e8, 1e8 - 1, 0), (0, 0, 1))) == -1.0 exactly
  ((1e8 + 1)(1e8 - 1) - 1e16 = -1; naive floating point gives 0 or -2);
- scale: inverse(1e-200 * A) == 1e200 * inverse(A) within 1e-15 relative, and inverse((1e60 / 3) * A) works; the singularity test does not depend on the scale:
  1e-200 * identity is invertible;
- results are tuples of tuples of floats (or a float, or a bool for is_rotation: `is True` / `is False`); lists and tuples are both accepted, ints and fractions.Fraction too.

Limits (state them): BIG == 1e60, SINGULAR == 1e-12. Refusals (ValueError): a matrix that is not a list or tuple of three rows of three numbers (two rows, four rows,
a row of two, a flat list of nine, a string, None, a number); an entry that is a bool, a string, None, nan, inf, a complex or beyond 1e60 (1.0000001e60); a vector of the
wrong length or type in matvec; inverse of a singular matrix ([[1, 2, 3], [2, 4, 6], [1, 0, 1]], the zero matrix) or of a nearly singular one (diag(1, 1, 1e-13): refused;
diag(1, 1, 1.1e-12): accepted) with a message containing "singular"; inverse that overflows (1e-320 * identity): "overflows"; is_rotation with tol 0, negative, above 1,
nan, True or a string.
