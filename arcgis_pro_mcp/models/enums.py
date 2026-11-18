"""Enumerations for ArcGIS Pro MCP Server parameters and types."""

from enum import Enum


class GeometryType(str, Enum):
    """Supported ArcGIS feature class geometry types."""
    POINT = "POINT"
    MULTIPOINT = "MULTIPOINT"
    POLYLINE = "POLYLINE"
    POLYGON = "POLYGON"
    MULTIPATCH = "MULTIPATCH"


class FieldType(str, Enum):
    """Supported ArcPy attribute field types."""
    TEXT = "TEXT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    SHORT = "SHORT"
    LONG = "LONG"
    DATE = "DATE"
    BLOB = "BLOB"
    GUID = "GUID"


class LineSide(str, Enum):
    """Side of feature to buffer."""
    FULL = "FULL"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    OUTSIDE_ONLY = "OUTSIDE_ONLY"


class LineEndType(str, Enum):
    """Shape of buffer ends."""
    ROUND = "ROUND"
    FLAT = "FLAT"


class DissolveOption(str, Enum):
    """Dissolve options for buffering and aggregation."""
    NONE = "NONE"
    ALL = "ALL"
    LIST = "LIST"


class SpatialRelationship(str, Enum):
    """Spatial relationship types for select by location and spatial join."""
    INTERSECT = "INTERSECT"
    WITHIN_A_DISTANCE = "WITHIN_A_DISTANCE"
    CONTAINS = "CONTAINS"
    COMPLETELY_CONTAINS = "COMPLETELY_CONTAINS"
    WITHIN = "WITHIN"
    COMPLETELY_WITHIN = "COMPLETELY_WITHIN"
    ARE_IDENTICAL_TO = "ARE_IDENTICAL_TO"
    BOUNDARY_TOUCHES = "BOUNDARY_TOUCHES"
    SHARE_A_LINE_SEGMENT_WITH = "SHARE_A_LINE_SEGMENT_WITH"
    CROSSED_BY_THE_OUTLINE_OF = "CROSSED_BY_THE_OUTLINE_OF"
    HAVE_THEIR_CENTER_IN = "HAVE_THEIR_CENTER_IN"


class RasterExportFormat(str, Enum):
    """Map and layout export formats."""
    PNG = "PNG"
    JPEG = "JPEG"
    JPG = "JPG"
    PDF = "PDF"
    TIFF = "TIFF"


class SlopeMeasurement(str, Enum):
    """Measurement units for slope analysis."""
    DEGREE = "DEGREE"
    PERCENT_RISE = "PERCENT_RISE"


class AspectMethod(str, Enum):
    """Calculation method for terrain aspect."""
    PLANAR = "PLANAR"
    GEODESIC = "GEODESIC"


class SymbologyRendererType(str, Enum):
    """Supported layer symbology renderer types in ArcGIS Pro."""
    SIMPLE = "SimpleRenderer"
    UNIQUE_VALUE = "UniqueValueRenderer"
    GRADUATED_COLORS = "GraduatedColorsRenderer"
    GRADUATED_SYMBOLS = "GraduatedSymbolsRenderer"
    UNCLASSED_COLORS = "UnclassedColorsRenderer"


class ClassificationMethod(str, Enum):
    """Classification methods for graduated colors and graduated symbols."""
    NATURAL_BREAKS = "NaturalBreaks"
    EQUAL_INTERVAL = "EqualInterval"
    QUANTILE = "Quantile"
    GEOMETRIC_INTERVAL = "GeometricInterval"
    DEFINED_INTERVAL = "DefinedInterval"
    STANDARD_DEVIATION = "StandardDeviation"


class BasemapName(str, Enum):
    """Recognized built-in gallery and custom basemaps."""
    TOPOGRAPHIC = "Topographic"
    IMAGERY = "Imagery"
    STREETS = "Streets"
    NAVIGATION = "Navigation"
    LIGHT_GRAY_CANVAS = "Light Gray Canvas"
    DARK_GRAY_CANVAS = "Dark Gray Canvas"
    OCEANS = "Oceans"
    TERRAIN_WITH_LABELS = "Terrain with Labels"
    STREETS_NIGHT = "Streets (Night)"
    GOOGLE_SATELLITE = "Google Satellite"
    GOOGLE_HYBRID = "Google Hybrid"
    GOOGLE_ROADS = "Google Roads"
    GOOGLE_TERRAIN = "Google Terrain"
    OPENSTREETMAP = "OpenStreetMap"
    CARTODB_DARK = "CartoDB Dark"
    CARTODB_LIGHT = "CartoDB Light"


class ExtensionAction(str, Enum):
    """Actions for managing ArcGIS Pro extensions."""
    STATUS = "status"
    CHECK_OUT = "check_out"
    CHECK_IN = "check_in"
