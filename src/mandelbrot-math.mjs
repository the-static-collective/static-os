/* Mathematical Mandelbrot orbit, not a symbolic visualization.
 * z_0 = 0; z_(n+1) = z_n² + c. Escape radius squared = 256.
 * No actual iteration can prove membership in the set at finite maxIter.
 */
export function mandelbrotEscape(re,im,maxIter=128){
  if(!Number.isFinite(re)||!Number.isFinite(im)||
     !Number.isSafeInteger(maxIter)||maxIter<1||maxIter>4096)
    throw new TypeError('MANDELBROT_ARGUMENTS_INVALID');
  let zr=0,zi=0,zr2=0,zi2=0,n=0;
  while(n<maxIter&&zr2+zi2<=256){
    zi=2*zr*zi+im;
    zr=zr2-zi2+re;
    zr2=zr*zr;zi2=zi*zi;n++;
  }
  return {iterations:n,zr,zi,escaped:n<maxIter};
}
