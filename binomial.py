# Provides a implementation of the binomial asset pricing model,
# as well as specific classes to represent American and European call
# and put options

from math import exp, sqrt

# General Implementation
class Stock:
    def __init__(self, spot, vol):
        """
        spot: a float, the current price of the stock
        vol: a float, the volatility of the stock
            (assuming lognormal distribution of prices)
        """
        self.spot = spot
        self.vol = vol

class Option:
    def __init__(self, underlying, expiry):
        """
        underlying: a Stock, the asset on which the option is written
        expiry: a float, the time, in years, until expiration of the option
        """
        self.underlying = underlying
        self.expiry = expiry

    def final_payoff(self, spot):
        raise NotImplementedError("Final option payoff is not defined")

    def early_payoff(self, spot):
        raise NotImplementedError("Early exercise payoff is not defined")

class BinomialModel:
    def __init__(self, option, r):
        """
        option: an Option, the option to be priced
        r: a float, the continuous annual risk-free interest rate, as a decimal
        """
        self.option = option
        self.r = r

    def price(self, N=500):
        """
        Computes the price of the option using the binomial asset pricing model

        Arguments:
        N: an integer, the number of steps to take in the model

        Returns:
        The computed price of the option, a float
        """
        # Compute model parameters
        dt = self.option.expiry/N   # Step size
        u =  exp(self.option.underlying.vol * sqrt(dt)) # Up movment
        d = 1/u
        p = (exp(self.r * dt) - d)/(u - d) # Risk-neutral probability

        # Computes the price of the underlying asset k steps into the tree
        # with m up movements
        def S(k,m):
            return self.option.underlying.spot * (u ** (2*m-k))

        # Builds the pricing tree.  Will be a dictionary, where
        # C[(k,m)] is the value of the option at the node
        # that is k steps into the tree with m up movements
        C = {}

        # Find values of the option at expiration
        for m in range(0, N+1):
            C[(N, m)] = self.option.final_payoff(S(N,m))

        # Find value of the option at interior nodes
        # future_value is discounted expected future value of the option
        #    assuming risk neutral probability
        # exercise_value is the value of the option from early exercise
        for k in range(N-1, -1, -1):
            for m in range(0,k+1):
                future_value = exp(-self.r * dt) * (p * C[(k+1, m+1)] + (1-p) * C[(k+1, m)])
                exercise_value = self.option.early_payoff(S(k,m))
                C[(k, m)] = max(future_value, exercise_value)
        return C[(0,0)]


# Classes to encode American and European call and put options, all inheriting
# from the Options class above.  Other option types (e.g., straddle) can be
# priced by implementing them as subclasses of Option.
class EuroCall(Option):
    def __init__(self, underlying, expiry, strike):
        """
        strike: a float, the strike price of the asset
        """
        super().__init__(underlying, expiry)
        self.strike = strike

    def final_payoff(self, spot):
        # Standard payoff function for a call option
        return max(spot - self.strike,0)

    def early_payoff(self, spot):
        # Returns zero since European call options cannot be exercised early
        return 0

class EuroPut(Option):
    def __init__(self, underlying, expiry, strike):
        """
        strike: a float, the strike price of the asset
        """
        super().__init__(underlying, expiry)
        self.strike = strike

    def final_payoff(self, spot):
        # Standard payoff for a put option
        return max(self.strike - spot,0)

    def early_payoff(self, spot):
        # Returns zero since European put options cannot be exercised early
        return 0

class AmerCall(EuroCall):
    def early_payoff(self, spot):
        # American options can be exercised early with the same payoff
        # as at expiration
        return self.final_payoff(spot)

class AmerPut(EuroPut):
    def early_payoff(self, spot):
        # American options can be exercised early with the same payoff
        # as at expiration
        return self.final_payoff(spot)
