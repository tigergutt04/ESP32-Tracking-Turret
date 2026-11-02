def find_target(boxes):
    """Finner sentrum av målet (første boks fra YOLO). Gir (xt, yt) i piksler, eller None hvis ingen mål."""
    if len(boxes) == 0:
        return None

    # xyxy = hjørnene på boksen: (x1, y1) øverst til venstre, (x2, y2) nederst til høyre.
    # [0] = boksen YOLO er sikrest på.
    x1, y1, x2, y2 = boxes.xyxy[0].tolist()

    xt = (x1 + x2) / 2      # Målets sentrum langs x-aksen
    yt = (y1 + y2) / 2      # Målets sentrum langs y-aksen

    return xt, yt


def system_error(xt, yt, width, height):
    """System error, ligning (1): e = bildets sentrum - målets posisjon. Gir (ex, ey) i piksler."""
    xc = width / 2          # Bildets sentrum langs x-aksen
    yc = height / 2         # Bildets sentrum langs y-aksen

    # ex > 0: målet er til venstre for sentrum. ey > 0: målet er over sentrum (y-aksen i bilder peker nedover).
    ex = xc - xt
    ey = yc - yt
    return ex, ey
