# Exporters

Exports go through the `get_exporter` factory, which returns a `BaseExporter` subclass for the requested format. Call its `export` method with an output path. The output of each format is described in [Export Formats](../export-formats.md).

## Registry

::: recursivist.exporters

## Base Exporter

::: recursivist.exporters.base
