"""CutoverProof orchestration package.

The CLI is deliberately not imported here. Eagerly importing it makes
``python -m src.coordinator.cli`` execute a module that is already present in
``sys.modules``, producing a runtime warning in clean reproduction output.
"""
