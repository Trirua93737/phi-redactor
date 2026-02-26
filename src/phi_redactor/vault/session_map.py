"""In-memory cache backed by the vault DB for fast token lookups.

``SessionTokenMap`` sits in front of :class:`PhiVault` and keeps a
per-session dictionary of original-to-synthetic (and reverse) mappings
in memory.  Cache misses fall through to the encrypted SQLite vault,
and new mappings are written through to both layers.
"""

from __future__ import annotations

from collections.abc import Callable

from phi_redactor.vault.store import PhiVault


class SessionTokenMap:
    """In-memory cache backed by vault DB for fast token lookups.

    Parameters
    ----------
    vault:
        The :class:`PhiVault` instance used for persistent storage.
    """

    def __init__(self, vault: PhiVault) -> None:
        self._vault = vault
        # session_id -> {original: synthetic}
        self._cache: dict[str, dict[str, str]] = {}
        # session_id -> {synthetic: original}
        self._reverse: dict[str, dict[str, str]] = {}

    def get_or_create_synthetic(
        self,
        session_id: str,
        original: str,
        category: str,
        generate_fn: Callable[[], str],
    ) -> str:
        """Return the synthetic token for *original*, creating one if needed.

        Resolution order:
        1. In-memory forward cache.
        2. Vault database (``lookup_by_original``).
        3. Generate via *generate_fn*, persist to vault and both caches.

        Parameters
        ----------
        session_id:
            Active session identifier.
        original:
            The original PHI string.
        category:
            PHI category label (e.g. ``"PERSON_NAME"``).
        generate_fn:
            Zero-argument callable that produces a new synthetic value.
        """
        # 1. Memory cache hit?
        session_fwd = self._cache.get(session_id)
        if session_fwd is not None:
            synthetic = session_fwd.get(original)
            if synthetic is not None:
                return synthetic

        # 2. Vault DB lookup.
        synthetic = self._vault.lookup_by_original(session_id, original)
        if synthetic is not None:
            self._put_cache(session_id, original, synthetic)
            return synthetic

        # 3. Generate, persist, cache.
        synthetic = generate_fn()
        self._vault.store_mapping(session_id, original, synthetic, category)
        self._put_cache(session_id, original, synthetic)
        return synthetic

    def get_original(self, session_id: str, synthetic: str) -> str | None:
        """Return the original PHI for a synthetic token, or *None*.

        Resolution order:
        1. In-memory reverse cache.
        2. Vault database (``lookup_by_synthetic``).
        """
        session_rev = self._reverse.get(session_id)
        if session_rev is not None:
            original = session_rev.get(synthetic)
            if original is not None:
                return original

        original = self._vault.lookup_by_synthetic(session_id, synthetic)
        if original is not None:
            self._put_cache(session_id, original, synthetic)
        return original

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _put_cache(self, session_id: str, original: str, synthetic: str) -> None:
        """Insert into both forward and reverse caches."""
        self._cache.setdefault(session_id, {})[original] = synthetic
        self._reverse.setdefault(session_id, {})[synthetic] = original
