from shapely.geometry import MultiPolygon, Polygon, base, polygon


def reorient(shape: base.BaseGeometry, orientation=-1) -> base.BaseGeometry:
    if isinstance(shape, Polygon):
        return polygon.orient(shape, orientation)
    if isinstance(shape, MultiPolygon):
        return MultiPolygon(reorient(p) for p in shape)
    return shape
