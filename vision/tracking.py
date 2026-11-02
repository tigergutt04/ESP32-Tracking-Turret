FACE_POINTS = [0, 1, 2, 3, 4]     # Pose-punkter i ansiktet: nese, venstre/høyre øye, venstre/høyre øre
POINT_CONF = 0.5                  # Et punkt må være minst 50 % sikkert for å brukes


def find_target(result):
    """Finner ansiktet til personen YOLO er sikrest på. Gir (xt, yt) i piksler, eller None hvis ingen mål."""
    if len(result.boxes) == 0:
        return None

    # keypoints.xy[0] = (x, y) for de 17 punktene på den første personen, keypoints.conf[0] = hvor sikre de er
    points = result.keypoints.xy[0].tolist()
    confs = result.keypoints.conf[0].tolist() if result.keypoints.conf is not None else [0] * len(points)

    # 1. Nesen, hvis den synes
    if confs[0] > POINT_CONF:
        return points[0][0], points[0][1]

    # 2. Ellers gjennomsnittet av øyne og ører som synes (f.eks. når personen snur seg)
    visible = [points[i] for i in FACE_POINTS if confs[i] > POINT_CONF]
    if visible:
        xt = sum(p[0] for p in visible) / len(visible)
        yt = sum(p[1] for p in visible) / len(visible)
        return xt, yt

    # 3. Ellers øvre del av boksen, der hodet som regel er
    # xyxy = hjørnene på boksen: (x1, y1) øverst til venstre, (x2, y2) nederst til høyre
    x1, y1, x2, y2 = result.boxes.xyxy[0].tolist()
    xt = (x1 + x2) / 2              # Midt på i bredden
    yt = y1 + 0.15 * (y2 - y1)      # 15 % ned fra toppen av boksen
    return xt, yt


def system_error(xt, yt, width, height):
    """System error, ligning (1): e = bildets sentrum - målets posisjon. Gir (ex, ey) i piksler."""
    xc = width / 2          # Bildets sentrum langs x-aksen
    yc = height / 2         # Bildets sentrum langs y-aksen

    # ex > 0: målet er til venstre for sentrum. ey > 0: målet er over sentrum (y-aksen i bilder peker nedover).
    ex = xc - xt
    ey = yc - yt
    return ex, ey
