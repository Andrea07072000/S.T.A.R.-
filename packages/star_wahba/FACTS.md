# Published values the tests of star_wahba may cite (checked by the reviewer against the computation)

1. Wahba's problem (G. Wahba, "A least squares estimate of satellite attitude", SIAM Review 7, 1965, problem 65-1): find the proper orthogonal matrix A that minimises
   L(A) = 0.5 sum of w_i |b_i - A r_i|^2 (weights normalised here to sum 1) over unit vectors r_i (reference frame) and b_i (body frame). Davenport's q-method (1968; in Markley and Crassidis, Fundamentals of
   Spacecraft Attitude Determination and Control, section 5.3): with B = sum w_i b_i r_i^T, S = B + B^T, sigma = trace(B), z = (B23 - B32, B31 - B13, B12 - B21), the optimal
   quaternion is the eigenvector of the largest eigenvalue of K = [[S - sigma I, z], [z^T, sigma]], and the loss at the optimum is 1 - (largest eigenvalue) for weights that sum to 1.
   TRIAD (H. D. Black, 1964): from two pairs, with t1 = r1, t2 = r1 x r2 normalised, t3 = t1 x t2 and the same s1, s2, s3 in the body, A = s1 t1^T + s2 t2^T + s3 t3^T.
   No numerical example from these sources is cited: the numbers below are derived by hand.

Values derivable by hand (write the derivation in a comment):
- convention: b = A r takes a direction from the REFERENCE frame to the BODY frame; triad(r1, r2, b1, b2) and rotation_matrix(q) return a tuple of three rows of three floats;
  q_method(refs, bodies, weights=None) returns the tuple (w, x, y, z), scalar first, unit norm, w >= 0; wahba_loss(q, refs, bodies, weights=None) returns a float >= 0;
- a body frame turned by +90 deg about z sees the reference x axis along its -y axis: A = ((0, 1, 0), (-1, 0, 0), (0, 0, 1)); its quaternion is (cos 45, 0, 0, sin 45):
  rotation_matrix((0.7071067811865476, 0, 0, 0.7071067811865476)) is that matrix within 3e-16; with refs = [(1, 0, 0), (0, 1, 0)] and bodies = [(0, -1, 0), (1, 0, 0)]
  both triad and rotation_matrix(q_method(...)) give that matrix within 1e-15, and q_method gives (0.7071067811865476, 0, 0, 0.7071067811865476) within 1e-15;
- identity: equal reference and body directions give the identity matrix and the quaternion (1, 0, 0, 0) (within 1e-15);
- a half turn about x: refs [(0, 1, 0), (0, 0, 1)], bodies [(0, -1, 0), (0, 0, -1)] give A = diag(1, -1, -1) and q = (0, 1, 0, 0) up to the sign rule (w is 0: the vector part may
  come with either sign; compare through rotation_matrix);
- rotation_matrix of the quaternion of a turn by an angle t about x is ((1, 0, 0), (0, cos t, sin t), (0, -sin t, cos t)) [q = (cos t/2, sin t/2, 0, 0)]; about y:
  ((cos t, 0, -sin t), (0, 1, 0), (sin t, 0, cos t)); q and -q give the same matrix exactly; a quaternion that is not unit is normalised: (2, 0, 0, 0) gives the identity;
- every matrix returned is proper orthogonal: A A^T = I within 1e-14 and determinant +1 within 1e-14;
- only directions count: scaling any reference or body vector by a positive factor changes nothing (within 1e-15); weights are relative: multiplying all by 7 changes nothing;
- noise-free observations are reproduced: for any attitude A0 and directions r_i not all parallel, with b_i = A0 r_i, triad and the q-method return A0 within 1e-12 (directions at
  least 20 deg apart) and wahba_loss at the solution is below 1e-25;
- TRIAD matches the FIRST pair exactly and the second only in the plane: with b2 perturbed, A r1 is still b1 (within 1e-15) while the q-method spreads the error;
  swapping the two pairs changes the TRIAD answer when the data are inconsistent, and does not when they are consistent;
- the q-method is the minimum: for noisy data, wahba_loss at q_method(...) is not larger than at 200 random quaternions nor at the quaternion turned by 1e-4 rad about any axis;
  the weights are normalised to sum 1 before the loss is formed, so the loss is at most 2 and does not depend on the scale of the weights;
  with two observations of equal weight whose angular separations differ by d (inconsistent data) the optimum leaves each direction d/2 away and the loss is 1 - cos(d / 2):
  for separations of 90 deg in the reference and 80 deg in the body, 1 - cos(5 deg) = 0.0038053019082545 within 1e-14;
- a large weight pulls the solution: with weights (1e6, 1) the q-method leaves the first direction off by (w2 / w1) sin(inconsistency) to first order
  (1e-6 * sin(10 deg) = 1.7365e-7 rad in the example above), approaching TRIAD.

Limits (state them): MAX_PAIRS == 1000, PARALLEL == 1e-12. Refusals (ValueError):
- a vector that is not a list or tuple of 3 numbers (2 or 4 numbers, a string, None), that holds a bool, a string, nan or inf, or that is zero ("zero vector");
- triad: r1 parallel or opposite to r2, or b1 to b2 ("parallel");
- q_method and wahba_loss: refs and bodies of different lengths or not lists ("same length"); fewer than 2 pairs or more than 1000 ("between 2 and 1000");
  weights of another length ("as many as the pairs"), or 0, negative, nan, inf, a bool ("positive finite");
- q_method: all reference directions parallel (two pairs with the same reference direction; or one direction repeated), "do not fix an attitude";
- rotation_matrix and wahba_loss: q that is not 4 numbers, holds nan, inf or a bool, or is (0, 0, 0, 0) ("zero quaternion").
