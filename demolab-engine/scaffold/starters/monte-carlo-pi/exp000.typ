#import "/demolab-engine/build/lib.typ": numbers-table, provenance-footer, data-file

#let meta = (
  title: "Estimating π by throwing darts",
  date: "2026-07-10",
  description: "A Monte Carlo estimate of π: sample points in the unit square, count the fraction inside the quarter circle.",
  collection: "monte-carlo",
  status: "final",
)

#let run = json(data-file("exp000/numbers.json"))

#let body = [
  Throw a large number of random points at the unit square and some fraction land inside
  the quarter circle of radius one. That fraction is the ratio of the two areas —
  $(pi\/4)$ for the quarter disc against $1$ for the square — so multiplying it by four
  estimates $pi$. It is the simplest useful Monte Carlo method: no cleverness, just
  counting, and the answer sharpens as you throw more darts.

  == Method

  Draw $N$ points $(x, y)$ with $x, y tilde.op "Uniform"(0, 1)$ independently, and count a
  point as *inside* when it falls within the quarter circle:
  $ x^2 + y^2 <= 1. $
  The estimator is
  $ hat(pi) = 4 dot.op frac(N_"inside", N), $
  where
  - $N$ is the total number of sampled points,
  - $N_"inside"$ is the number of points satisfying $x^2 + y^2 <= 1$,
  - $hat(pi)$ is the resulting estimate of $pi$.

  The sample is drawn from a seeded generator, so the run reproduces bit-for-bit. Its
  error shrinks like $1 \/ sqrt(N)$ — the generic Monte Carlo rate — so each extra digit
  of accuracy costs roughly a hundredfold more points.

  == Results

  With $N = #run.pi.config.n$ points, the estimate is
  #calc.round(run.pi.pi_estimate, digits: 5), off the true value by
  #calc.round(run.pi.absolute_error, digits: 5). Of the sampled points,
  #run.pi.inside_count fell inside the quarter circle.

  #figure(
    image(data-file("exp000/scatter.png"), width: 70%),
    caption: [A subsample of the thrown points: those inside the quarter circle (black)
      against those outside (grey), with the arc $x^2 + y^2 = 1$ in red. The estimate is
      four times the inside fraction.],
  )

  As points accumulate the running estimate wanders at first, then settles toward $pi$
  (dashed line). The horizontal axis is logarithmic, so each equal step rightward is a
  tenfold increase in samples — and the curve visibly tightens across each one.

  #figure(
    image(data-file("exp000/convergence.svg"), width: 100%),
    caption: [Running estimate of $pi$ against the number of points thrown (log scale),
      converging on the true value (red dashed) as the sample grows.],
  )

  #numbers-table(run.pi, title: "Run parameters and results")

  #provenance-footer(run.pi.config)
]
