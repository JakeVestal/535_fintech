export type Fit = {
  n: number;
  slope: number;
  intercept: number;
  r2: number;
  xMin: number;
  xMax: number;
};

export function ordinaryLeastSquares(xs: number[], ys: number[]): Fit | null {
  const n = Math.min(xs.length, ys.length);
  if (n < 2) return null;
  let sx = 0;
  let sy = 0;
  let sxx = 0;
  let sxy = 0;
  let xMin = Infinity;
  let xMax = -Infinity;
  for (let i = 0; i < n; i++) {
    const x = xs[i];
    const y = ys[i];
    sx += x;
    sy += y;
    sxx += x * x;
    sxy += x * y;
    xMin = Math.min(xMin, x);
    xMax = Math.max(xMax, x);
  }
  const denom = n * sxx - sx * sx;
  const slope = denom === 0 ? 0 : (n * sxy - sx * sy) / denom;
  const intercept = (sy - slope * sx) / n;
  const meanY = sy / n;
  let ssTot = 0;
  let ssRes = 0;
  for (let i = 0; i < n; i++) {
    const y = ys[i];
    const hat = intercept + slope * xs[i];
    ssTot += (y - meanY) ** 2;
    ssRes += (y - hat) ** 2;
  }
  const r2 = ssTot === 0 ? 1 : 1 - ssRes / ssTot;
  return { n, slope, intercept, r2, xMin, xMax };
}
