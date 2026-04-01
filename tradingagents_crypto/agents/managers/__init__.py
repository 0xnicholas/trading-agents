"""Portfolio managers."""

from tradingagents_crypto.agents.managers.crypto_portfolio_manager import (
    CryptoPortfolioManager,
    CryptoPosition,
)


def create_portfolio_manager(config: dict):
    """
    Factory function to create the appropriate portfolio manager.

    Args:
        config: Configuration dict with optional "mode" key
            - config["mode"] = "crypto" -> CryptoPortfolioManager
            - otherwise -> raises NotImplementedError (stock mode not in scope)

    Returns:
        PortfolioManager instance

    Raises:
        NotImplementedError: If stock mode is requested (out of scope for Phase 3)
    """
    mode = config.get("mode", "crypto")

    if mode == "crypto":
        return CryptoPortfolioManager(config)
    else:
        raise NotImplementedError(
            f"Portfolio manager for mode '{mode}' not implemented. "
            "Only 'crypto' mode is supported in Phase 3."
        )


__all__ = [
    "CryptoPortfolioManager",
    "CryptoPosition",
    "create_portfolio_manager",
]
