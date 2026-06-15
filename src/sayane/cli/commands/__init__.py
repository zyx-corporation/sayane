"""Command group modules for the Sayane CLI.

This package is introduced for #172 so command registration can be moved out of
``sayane.cli.app`` by responsibility boundary.

Keep the migration mechanical:

- preserve command names
- preserve option names
- preserve output text
- preserve golden-backed export behavior
- preserve candidate lifecycle behavior
- preserve Git auto-commit behavior
"""
