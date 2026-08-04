"""HERACLES — special-agent mission software (No Time to Die, 2021).

Pure domain core for the bond film package ``no_time_to_die``: a DNA-targeted
bioweapon countermeasure model, poison-garden toxicology, and poison-delivery
forensics. The domain modules below are infrastructure-free and importable
without bond-api; :mod:`no_time_to_die.mission` is the thin adapter that binds
them to the frozen mission protocol.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
