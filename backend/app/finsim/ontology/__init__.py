"""FINsim ontology module — schema, loader, and population."""

from .ontology_loader import OntologyLoader
from .populate_finsim import populate_s0

__all__ = ['OntologyLoader', 'populate_s0']
