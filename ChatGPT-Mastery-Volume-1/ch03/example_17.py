import sympy as sp
import mpmath

# Configure arbitrary precision to 100 decimal digits
mpmath.mp.dps = 100

def arbitrary_precision_black_scholes(S, K, T, r, sigma):
    """Computes Black-Scholes call price with 100 digits of analytical precision."""
    S = mpmath.mpf(S)
    K = mpmath.mpf(K)
    T = mpmath.mpf(T)
    r = mpmath.mpf(r)
    sigma = mpmath.mpf(sigma)

    d1 = (mpmath.log(S / K) + (r + (sigma**2) / 2) * T) / (sigma * mpmath.sqrt(T))
    d2 = d1 - sigma * mpmath.sqrt(T)

    # Standard Gaussian Cumulative Distribution via error function
    N_d1 = 0.5 * (1 + mpmath.erf(d1 / mpmath.sqrt(2)))
    N_d2 = 0.5 * (1 + mpmath.erf(d2 / mpmath.sqrt(2)))

    call_price = S * N_d1 - K * mpmath.exp(-r * T) * N_d2
    return call_price

# Calculate deep out-of-the-money option price
price = arbitrary_precision_black_scholes(S=100.0, K=350.0, T=0.25, r=0.05, sigma=0.20)
print(f"100-Digit Precision Call Price:\n{price}")
